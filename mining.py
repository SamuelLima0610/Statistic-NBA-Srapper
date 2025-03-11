import time
from communication_api import Api
from constants import GAME_COLUMNS, TEAMS
from site_processor import SiteProcessor
from threading import Thread
from time import perf_counter
from datetime import datetime


MONTHES = {'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6}
URL = "https://www.basketball-reference.com/"

class Mining(Thread):

    def __init__(self, monthes, years, r, q, tabel, thread_id):
        super().__init__()
        self.monthes = monthes
        self.api = Api()
        self.html_processor = SiteProcessor()
        self.years = years
        self.games = []
        self.r = r
        self.q = q
        self.tabel = tabel
        self.thread_id = thread_id

    def update_interface(self, begin, end, game, status):
        time = end - begin
        self.q.put(time)
        self.r.event_generate('<<Updated>>', when='tail')
        self.tabel.insert('', 0, values=(self.thread_id, game, status))

    def calculate_the_amount_of_games(self):
        for year in self.years:
            self.__insert_season(f'{year}')
            for month in self.monthes:
                try:
                    response = self.html_processor.get_html(URL, f"leagues/NBA_{year}_games-{month}.html")
                    time.sleep(30)
                    games = self.html_processor.get_info_from_table(response.text, 'schedule')
                    games = [game for game in games if "Pontos" in game.keys()]
                    self.games += games
                except:
                    break
        return len(self.games)

    def __insert_team(self, teams_name):
        team = self.api.send_request('POST', '/team', object_json={'nome': teams_name})
        return team['codigo_equipe']
    
    def __insert_season(self, season):
        season = self.api.send_request('POST', '/season', object_json={'periodo': season})
        self.season_code = season['codigo_temporada']
    
    def get_info_game(self, html, is_home_team):
        scorebox = self.html_processor.get_element_by_class(html, 'div', 'scorebox') 
        teams_name = self.html_processor.get_team(scorebox, is_home_team)
        team_score = self.html_processor.get_scorebox(scorebox, is_home_team)
        team_info_game = self.html_processor.get_info_from_table(html, f'box-{TEAMS[teams_name]}-game-basic', ['', 'Basic Box Score Stats']) 
        return {
            'team': teams_name,
            'score': team_score,
            'player_stats': team_info_game,
            'home': is_home_team,
            'acronym': TEAMS[teams_name]
        }

    def __process_date(self, date):
        split_date = date.split(',')
        month = split_date[1].strip().split(' ')[0]
        day = split_date[1].strip().split(' ')[1]
        month = MONTHES[month]
        return datetime.strptime(f"{split_date[2].strip()}-{month}-{day}",'%Y-%m-%d')

    def __insert_player_api(self, team_code, players_info):
        try:
            players_info['Player']['text'].index("'")
            players_name = players_info['Player']['text'].replace("'", "") 
        except:
            players_name = players_info['Player']['text']
        if players_info['Player']['href'][0] == '/':
            path = players_info['Player']['href'][1:]
        else:
            path = players_info['Player']['href']
        response = self.html_processor.get_html(URL, path)
        time.sleep(30)
        nest_season_prevision = self.html_processor.get_info_from_table(response.text, 'totals_stats')
        team = self.api.send_request('POST', '/player', {
            'nome':players_name,
            'idade': nest_season_prevision[-1]['Age'],
            'codigo_equipe_atual': team_code,
        })
        return team['codigo_jogador']

    def __insert_player(self, team_code, players_info, players_game_info):
        try:
            time.sleep(3)
            player_code = self.__insert_player_api(team_code, players_info)
            players_game_info['codigo_jogador_fk'] = player_code
        except:
            pass

    def __process_time_on_court(self, player_info, key):
        minutos = player_info[key].split(':')[0]
        segundos = player_info[key].split(':')[1]
        player_info[key] = int(minutos) * 60 + int(segundos)
        player_info[key] = player_info[key]

    def __process_minus_plus_from_player(self, player_info, players_game_info, key):
        if player_info[key] == 0:
            players_game_info['contribuicao_foi_positiva'] = False
            return
        elif player_info[key] > 0:
            players_game_info['contribuicao_foi_positiva'] = True
        else:
            players_game_info['contribuicao_foi_positiva'] = False
        players_game_info[key] = player_info[key]
    
    def __insert_players_game_info(self, game_code, team_code, players_info):
        players_game_info = {"Codigo_jogo_fk": str(game_code)}
        for player_info in players_info['player_stats']:
            for key in player_info.keys():
                if key == "Player" and type(player_info[key]) == dict:
                    self.__insert_player(team_code, player_info, players_game_info)
                elif key in GAME_COLUMNS.values():
                    if key == 'Tempo_em_quadra':
                        if player_info[key] in ['Did Not Play','Did Not Dress', 'Not With Team', 'Player Suspended']:
                            return
                        self.__process_time_on_court(player_info, key)
                    elif key == 'Contribuicao':
                        self.__process_minus_plus_from_player(player_info, players_game_info, key)
                        continue
                    players_game_info[key] = player_info[key]
            self.api.send_request('POST', '/info_game', object_json=players_game_info)

    def __insert_game(self, date, home_team_info, guest_team_info):
        home_team_code = self.__insert_team(home_team_info['team'])
        guest_team_code = self.__insert_team(guest_team_info['team'])
        game = self.api.send_request('POST', '/game', object_json={
            'data_jogo': date.strftime('%d/%m/%Y %H:%M:%S'),
            'codigo_time_mandante': home_team_code,
            'codigo_temporada_jogo': self.season_code,
            'codigo_time_visitante': guest_team_code,
            'pontuacao_time_mandante': int(home_team_info["score"]),
            'pontuacao_time_visitante': int(guest_team_info["score"])
        })
        game_code = game['codigo_jogo']
        self.__insert_players_game_info(game_code, home_team_code, home_team_info)
        self.__insert_players_game_info(game_code, guest_team_code, guest_team_info)

    def run(self):
        game_infos = []
        for game in self.games:
            try:
                begin = perf_counter()
                response = self.html_processor.get_html(URL, game['Box Score'])
                time.sleep(30)
                game_info = {
                    'data': self.__process_date(game['Date']['text']),
                    'home': self.get_info_game(response.text, True),
                    'guest': self.get_info_game(response.text, False)
                }
                time.sleep(3)                
                game_infos.append(game_info)
                self.__insert_game(game_info['data'], game_info['home'], game_info['guest'])
                end = perf_counter()
                game = f'{game_info["guest"]["acronym"]}@{game_info["home"]["acronym"]}'
                self.update_interface(begin, end, game, 'Finalizado')
            except Exception as e:
                print(e)
                pass