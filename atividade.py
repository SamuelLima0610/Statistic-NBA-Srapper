import time as tempo
from datetime import datetime, timedelta, date
from banco_postgres import BancoDeDados
from processador_site import ProcessadorSite
from constantes import INFORMACAO_JOGO, TIMES, COLUNAS_EQUIPE, COLUNAS_JOGO, COLUNAS_TEMPORADA, COLUNAS_JOGADOR
from tqdm import tqdm
from threading import Thread


MESES = {'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6}
URL = "https://www.basketball-reference.com/"

class Atividade(Thread):

    def __init__(self, meses):
        super().__init__()
        self.meses = meses
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

    def __inserir_jogador(self, codigo_time, informacao_jogador):
        try:
            informacao_jogador['Player']['texto'].index("'")
            nome_jogador = informacao_jogador['Player']['texto'].replace("'", "") 
        except:
            nome_jogador = informacao_jogador['Player']['texto']
        pesquisa = self.banco.search(f"Select * from Jogador where Nome = '{nome_jogador}';", 1)
        if pesquisa is None:
            response = self.processador.pegar_html(URL, informacao_jogador['Player']['href'])
            projecao_prox_temporada = self.processador.pegar_linhas_tabela(response.text, 'totals')
            self.banco.insert(f'''INSERT INTO Jogador ({COLUNAS_JOGADOR}) VALUES ({codigo_time}, {projecao_prox_temporada[-1]['Age']}, '{nome_jogador}');''')
            pesquisa = self.banco.search(f"Select * from Jogador where Nome = '{nome_jogador}'", 1)
        return pesquisa[0]

    def __inserir_dados_do_jogo_jogador(self, codigo_jogo, codigo_time, informacao_jogadores):
        informacao_jogo_jogador = {"Codigo_jogo_fk": str(codigo_jogo)}
        for informacao_jogador in informacao_jogadores['informacao_jogadores_no_jogo']:
            for chave in informacao_jogador.keys():
                if chave == "Player" and type(informacao_jogador[chave]) == dict:
                    try:
                        tempo.sleep(3)
                        codigo_jogador = self.__inserir_jogador(codigo_time, informacao_jogador)
                        informacao_jogo_jogador['Codigo_jogador_fk'] = str(codigo_jogador)
                    except:
                        print("Oi")
                elif chave in INFORMACAO_JOGO.values():
                    if chave == 'Tempo_em_quadra':
                        if informacao_jogador[chave] in ['Did Not Play','Did Not Dress', 'Not With Team', 'Player Suspended']:
                            return
                        minutos = informacao_jogador[chave].split(':')[0]
                        segundos = informacao_jogador[chave].split(':')[1]
                        informacao_jogador[chave] = int(minutos) * 60 + int(segundos)
                        informacao_jogador[chave] = str(informacao_jogador[chave])
                    elif chave == 'Contribuicao':
                        if informacao_jogador[chave] == '0':
                            informacao_jogo_jogador['Contribuicao_foi_positiva'] = 'false'
                            informacao_jogo_jogador[chave] = '0'
                            continue
                        elif informacao_jogador[chave][0] == '+':
                            informacao_jogo_jogador['Contribuicao_foi_positiva'] = 'true'
                        else:
                            informacao_jogo_jogador['Contribuicao_foi_positiva'] = 'false'
                        informacao_jogo_jogador[chave] = informacao_jogador[chave][1:]
                        continue
                    informacao_jogo_jogador[chave] = informacao_jogador[chave]
            pesquisa = self.banco.search(f"Select * from informacao_jogador_por_jogo where Codigo_jogador_fk = {codigo_jogador} and Codigo_jogo_fk = {codigo_jogo};", 1)
            if pesquisa is None:
                colunas =','.join(informacao_jogo_jogador.keys())
                valores = ','.join(informacao_jogo_jogador.values())
                self.banco.insert(f'''INSERT INTO informacao_jogador_por_jogo ({colunas}) VALUES ({valores});''')

    def __inserir_jogo_no_banco(self, data, informacao_mandante, informacao_visitante):
        codigo_time_mandante = self.__inserir_time(informacao_mandante['time'])
        codigo_time_visitante = self.__inserir_time(informacao_visitante['time'])
        valores = f'{self.temporada_codigo}, {data}, {codigo_time_mandante}, {codigo_time_visitante}, {informacao_mandante["pontuacao"]}, {informacao_visitante["pontuacao"]}'
        pesquisa = self.banco.search(f"Select * from Jogo where Data = {data} and Codigo_time_mandante = {codigo_time_mandante}", 1)
        if pesquisa is None:
            self.banco.insert(f'''INSERT INTO Jogo ({COLUNAS_JOGO}) VALUES ({valores});''')
            pesquisa = self.banco.search(f"Select * from Jogo where Data = {data} and Codigo_time_mandante = {codigo_time_mandante}", 1)
        codigo_jogo = pesquisa[0]
        self.__inserir_dados_do_jogo_jogador(codigo_jogo, codigo_time_mandante, informacao_mandante)
        
    def run(self):
        anos = [2024]
        for ano in anos:
            self.__inserir_temporada(f'{ano}')
            for mes in self.meses:
                print(f'{mes}/{ano}')
                response = self.processador.pegar_html(URL, f"leagues/NBA_{ano}_games-{mes}.html")
                tempo.sleep(2)
                jogos = self.processador.pegar_linhas_tabela(response.text, 'schedule')
                for indice in tqdm(range(len(jogos))):
                    tempo.sleep(5)
                    response = self.processador.pegar_html(URL, jogos[indice]['Box Score'])
                    tempo.sleep(2)
                    informacao_jogo = {
                        'data': self.__processar_data(jogos[indice]['Date']['texto']),
                        'mandante': self.pegar_dados_dos_times_no_jogo(response.text, True),
                        'visitante': self.pegar_dados_dos_times_no_jogo(response.text, False)
                    }
                    self.__inserir_jogo_no_banco(informacao_jogo['data'], informacao_jogo['mandante'], informacao_jogo['visitante'])
        self.banco.fechar()
