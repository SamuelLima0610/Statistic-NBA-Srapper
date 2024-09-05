import time as tempo
from datetime import datetime, timedelta, date
from banco_postgres import BancoDeDados
from processador_site import ProcessadorSite
from constante_times_siglas import TIMES
from constantes_colunas_das_tabelas import COLUNAS_EQUIPE

class Atividade:

    def __init__(self):
        self.banco = BancoDeDados()
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
        #if not self.banco.existe_informacao(tabela, self.time):
        #    self.banco.existe_informacao(tabela, {'team':self.time, 'info': informacao_tabela})
        #elif self.jogou_ontem():
        #    self.banco.atualizar(tabela, informacao_tabela, self.time)
        print(informacao_tabela)

    def __inserir_time(self, nome_time):
        pesquisa = self.banco.search(f"Select * from Equipe where Nome = '{nome_time}'", 1)
        if pesquisa is None:
            self.banco.insert(f'''INSERT INTO Equipe ({COLUNAS_EQUIPE}) VALUES ('{nome_time}');''')

    def pegar_dados_dos_times_no_jogo(self, texto, mandante):
        scorebox = self.processador.pegar_elemento_por_classe(texto, 'div', 'scorebox') 
        nome_time = self.processador.pegar_time_no_scorebox(scorebox,mandante)
        pontuacao_time = self.processador.pegar_pontuacao_no_scorebox(scorebox,mandante)
        informacao_jogadores_times = self.processador.pegar_linhas_tabela(texto, f'box-{TIMES[nome_time]}-game-basic', ['', 'Basic Box Score Stats'])
        return {
            'time': nome_time,
            'pontuacao': pontuacao_time,
            'informacao_jogadores_no_jogo': informacao_jogadores_times,
            'mandante': mandante
        }

    def __inserir_no_banco(self, informacao):
        self.__inserir_time(informacao['time'])

    def executar(self):
        months = ['october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']
        years = [2024]
        for year in years:
            for month in months:
                URL = "https://www.basketball-reference.com/"
                response = self.processador.pegar_html(URL, f"leagues/NBA_{year}_games-{month}.html")
                tempo.sleep(2)
                jogos = self.processador.pegar_linhas_tabela(response.text, 'schedule')
                for jogo in jogos:
                    response = self.processador.pegar_html(URL, jogo['Box Score'])
                    tempo.sleep(2)
                    self.__inserir_no_banco(self.pegar_dados_dos_times_no_jogo(response.text, True))
                    self.__inserir_no_banco(self.pegar_dados_dos_times_no_jogo(response.text, False))
                    print("Oi")
        #self.banco.fechar_banco()
