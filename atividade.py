import time as tempo
from datetime import datetime, timedelta, date
from banco_postgres import BancoDeDados
from processador_site import ProcessadorSite
from constante_times_siglas import TIMES
from constantes_colunas_das_tabelas import COLUNAS_EQUIPE, COLUNAS_JOGO, COLUNAS_TEMPORADA

MESES = {'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'June': 6}

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
            pesquisa = self.banco.search(f"Select * from Equipe where Nome = '{nome_time}'", 1)
        return pesquisa[0]
    
    def __inserir_temporada(self, temporada):
        pesquisa = self.banco.search(f"Select * from Temporada where Periodo = '{temporada}'", 1)
        if pesquisa is None:
            self.banco.insert(f'''INSERT INTO Temporada ({COLUNAS_TEMPORADA}) VALUES ('{temporada}');''')
            pesquisa = self.banco.search(f"Select * from Temporada where Periodo = '{temporada}'", 1)
        self.temporada_codigo = pesquisa[0]
    
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

    def __processar_data(self, data):
        data_split = data.split(',')
        mes = data_split[1].strip().split(' ')[0]
        dia = data_split[1].strip().split(' ')[1]
        mes = MESES[mes]
        return f"'{data_split[2].strip()}-{mes}-{dia}'"

    def __inserir_jogo_no_banco(self, data, informacao_mandante, informacao_visitante):
        codigo_time_mandante = self.__inserir_time(informacao_mandante['time'])
        codigo_time_visitante = self.__inserir_time(informacao_visitante['time'])
        valores = f'{self.temporada_codigo}, {data}, {codigo_time_mandante}, {codigo_time_visitante}, {informacao_mandante["pontuacao"]}, {informacao_visitante["pontuacao"]}'
        pesquisa = self.banco.search(f"Select * from Jogo where Data = {data} and Codigo_time_mandante = {codigo_time_mandante}", 1)
        if pesquisa is None:
            self.banco.insert(f'''INSERT INTO Jogo ({COLUNAS_JOGO}) VALUES ({valores});''')
            pesquisa = self.banco.search(f"Select * from Jogo where Data = '{data}' and Codigo_time_mandante = {codigo_time_mandante}", 1)
        return pesquisa[0]
        
    def executar(self):
        meses = ['october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']
        anos = [2024]
        for ano in anos:
            self.__inserir_temporada(f'{ano}')
            for mes in meses:
                URL = "https://www.basketball-reference.com/"
                response = self.processador.pegar_html(URL, f"leagues/NBA_{ano}_games-{mes}.html")
                tempo.sleep(2)
                jogos = self.processador.pegar_linhas_tabela(response.text, 'schedule')
                for jogo in jogos:
                    response = self.processador.pegar_html(URL, jogo['Box Score'])
                    tempo.sleep(2)
                    self.__inserir_jogo_no_banco(self.__processar_data(jogo['Date']['texto']), self.pegar_dados_dos_times_no_jogo(response.text, True), self.pegar_dados_dos_times_no_jogo(response.text, False))
                    print("Oi")
        #self.banco.fechar_banco()
