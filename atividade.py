import time as tempo
from datetime import datetime, timedelta, date
from mongo import Mongo
from processador_site import ProcessadorSite

class Atividade:

    def __init__(self):
        self.banco = Mongo()
        self.processador = ProcessadorSite()

    def jogou_ontem(self):
        ultimo_jogo = None
        for index, jogo in enumerate(self.tabela_de_jogos):
            if 'Tm' in jogo.keys():
                if jogo['Tm'] == '':
                    ultimo_jogo = self.tabela_de_jogos[index-1] if index > 0 else self.tabela_de_jogos[0]
                    if ultimo_jogo == {'G': 'G'}:
                        ultimo_jogo = self.tabela_de_jogos[index-2]
                    break
        if ultimo_jogo is None:
            ultimo_jogo = self.tabela_de_jogos[-1]
        data_ultimo_jogo = datetime.strptime(ultimo_jogo['Date'], "%a, %b %d, %Y").date()
        ontem = date.today() - timedelta(days=1)
        if data_ultimo_jogo == ontem:
            return True
        return False

    def processar_informacao(self, tabela, pagina_html, escondida):
        if not escondida:
            informacao_tabela = self.processador.pegar_linhas_tabela(pagina_html, tabela)
        else:
            informacao_tabela = self.processador.pegar_tabela_escondida(pagina_html, tabela) 
        if not self.banco.existe_informacao(tabela, self.time):
            self.banco.existe_informacao(tabela, {'team':self.time, 'info': informacao_tabela})
        elif self.jogou_ontem():
            self.banco.atualizar(tabela, informacao_tabela, self.time)

    def executar(self):
        URL = "https://www.basketball-reference.com"
        response = self.processador.pegar_html(URL, "/teams/")
        tempo.sleep(2)
        infos_times = self.processador.pegar_linhas_tabela(response.text, 'teams_active')
        for info_time in infos_times:
            try:
                endpoint = info_time['Franchise']['href']
                self.time = endpoint.split('/')[-2]
                tempo.sleep(1.5)
                # verificar se jogou ontem
                response = self.processador.pegar_html(URL, f'/teams/{self.time}/2024_games.html')
                self.tabela_de_jogos = self.processador.pegar_linhas_tabela(response.text, 'div_games')
                tempo.sleep(2)
                response = self.processador.pegar_html(URL, endpoint)
                tempo.sleep(2)
                infos_time = self.processador.pegar_linhas_tabela(response.text, self.time)
                endpoint = infos_time[0]['Season']['href']
                response = self.processador.pegar_html(URL, endpoint)
                tempo.sleep(2)
                self.processar_informacao('totals', response.text, False)
                self.processar_informacao('team_and_opponent', response.text, True)
                self.processar_informacao('team_misc', response.text, True)
                self.processar_informacao('per_game', response.text, False)
            except Exception as e:
                print(e)
        self.banco.fechar_banco()
