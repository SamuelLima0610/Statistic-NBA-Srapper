import time as tempo
from db import Database
from site_processor import SiteProcessor
from constants import GAME_COLUMNS, TEAMS, COLUMNS_GAME, COLUMNS_SEASON, PLAYER_COLUMNS_DATABASE
from tqdm import tqdm
from threading import Thread


MONTHES = {'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6}
URL = "https://www.basketball-reference.com/"

class Mining(Thread):

    def __init__(self, monthes):
        super().__init__()
        self.monthes = monthes
        self.database = Database()
        self.html_processor = SiteProcessor()

    def __insert_team_db(self, teams_name):
        search = self.database.search(f"Select * from Equipe where Nome = '{teams_name}'", 1)
        if search is None:
            self.database.insert(f'''INSERT INTO Equipe ({COLUMNS_GAME}) VALUES ('{teams_name}');''')
            search = self.database.search(f"Select * from Equipe where Nome = '{teams_name}'", 1)
        return search[0]
    
    def __insert_season(self, season):
        search = self.database.search(f"Select * from Temporada where Periodo = '{season}'", 1)
        if search is None:
            self.database.insert(f'''INSERT INTO Temporada ({COLUMNS_SEASON}) VALUES ('{season}');''')
            search = self.database.search(f"Select * from Temporada where Periodo = '{season}'", 1)
        self.season_code = search[0]
    
    def get_info_game(self, html, is_home_team):
        scorebox = self.html_processor.get_element_by_class(html, 'div', 'scorebox') 
        teams_name = self.html_processor.get_team(scorebox, is_home_team)
        team_score = self.html_processor.get_scorebox(scorebox, is_home_team)
        team_info_game = self.html_processor.get_info_from_table(html, f'box-{TEAMS[teams_name]}-game-basic', ['', 'Basic Box Score Stats']) 
        return {
            'team': teams_name,
            'score': team_score,
            'player_stats': team_info_game,
            'home': is_home_team
        }

    def __process_date(self, date):
        split_date = date.split(',')
        month = split_date[1].strip().split(' ')[0]
        day = split_date[1].strip().split(' ')[1]
        month = MONTHES[month]
        return f"'{split_date[2].strip()}-{month}-{day}'"

    def __insert_player_db(self, team_code, players_info):
        try:
            players_info['Player']['text'].index("'")
            players_name = players_info['Player']['text'].replace("'", "") 
        except:
            players_name = players_info['Player']['text']
        search = self.database.search(f"Select * from Jogador where Nome = '{players_name}';", 1)
        if search is None:
            response = self.html_processor.get_html(URL, players_info['Player']['href'])
            nest_season_prevision = self.html_processor.get_info_from_table(response.text, 'totals')
            self.database.insert(f'''INSERT INTO Jogador ({PLAYER_COLUMNS_DATABASE}) VALUES ({team_code}, {nest_season_prevision[-1]['Age']}, '{players_name}');''')
            search = self.database.search(f"Select * from Jogador where Nome = '{players_name}'", 1)
        return search[0]

    def __insert_player(self, team_code, players_info, players_game_info):
        try:
            tempo.sleep(3)
            player_code = self.__insert_player_db(team_code, players_info)
            players_game_info['Codigo_jogador_fk'] = str(player_code)
        except:
            pass

    def __process_time_on_court(self, player_info, key):
        minutos = player_info[key].split(':')[0]
        segundos = player_info[key].split(':')[1]
        player_info[key] = int(minutos) * 60 + int(segundos)
        player_info[key] = str(player_info[key])

    def __process_minus_plus_from_player(self, player_info, players_game_info, key):
        if player_info[key] == '0':
            players_game_info['Contribuicao_foi_positiva'] = 'false'
            players_game_info[key] = '0'
            return
        elif player_info[key][0] == '+':
            players_game_info['Contribuicao_foi_positiva'] = 'true'
        else:
            players_game_info['Contribuicao_foi_positiva'] = 'false'
        players_game_info[key] = player_info[key][1:]

    def __insert_player_stats_game_db(self, players_game_info, game_code):
        search = self.database.search(f"Select * from informacao_jogador_por_jogo where Codigo_jogador_fk = {players_game_info['Codigo_jogador_fk']} and Codigo_jogo_fk = {game_code};", 1)
        if search is None:
            columns =','.join(players_game_info.keys())
            values = ','.join(players_game_info.values())
            self.database.insert(f'''INSERT INTO informacao_jogador_por_jogo ({columns}) VALUES ({values});''')
    
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
            self.__insert_player_stats_game_db(players_game_info, game_code)

    def __insert_game(self, date, home_team_info, guest_team_info):
        home_team_code = self.__insert_team_db(home_team_info['team'])
        guest_team_code = self.__insert_team_db(guest_team_info['team'])
        values = f'{self.season_code}, {date}, {home_team_code}, {guest_team_code}, {home_team_info["score"]}, {guest_team_info["score"]}'
        search = self.database.search(f"Select * from Jogo where Data = {date} and Codigo_time_mandante = {home_team_code}", 1)
        if search is None:
            self.database.insert(f'''INSERT INTO Jogo ({COLUMNS_GAME}) VALUES ({values});''')
            search = self.database.search(f"Select * from Jogo where Data = {date} and Codigo_time_mandante = {home_team_code}", 1)
        game_code = search[0]
        self.__insert_players_game_info(game_code, home_team_code, home_team_info)
        self.__insert_players_game_info(game_code, guest_team_code, guest_team_info)
        
    def run(self):
        years = [2024]
        for year in years:
            self.__insert_season(f'{year}')
            for month in self.monthes:
                print(f'{month}/{year}')
                response = self.html_processor.get_html(URL, f"leagues/NBA_{year}_games-{month}.html")
                tempo.sleep(2)
                games = self.html_processor.get_info_from_table(response.text, 'schedule')
                for indice in tqdm(range(len(games))):
                    tempo.sleep(5)
                    response = self.html_processor.get_html(URL, games[indice]['Box Score'])
                    tempo.sleep(2)
                    game_info = {
                        'data': self.__process_date(games[indice]['Date']['text']),
                        'home': self.get_info_game(response.text, True),
                        'guest': self.get_info_game(response.text, False)
                    }
                    self.__insert_game(game_info['data'], game_info['home'], game_info['guest'])
        self.database.close()
