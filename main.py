import requests
from header import HEADER
from bs4 import BeautifulSoup, Comment
import time as tempo

def pegar_linhas_tabela(text, id_tabela):
    soup = BeautifulSoup(text)
    tabela = soup.find(attrs={"id": id_tabela})
    cabecalho = tabela.find('thead')
    colunas_cabecalho = cabecalho.find_all('th')
    colunas = [coluna.text for coluna in colunas_cabecalho]
    corpos_tabela = tabela.find_all('tbody')
    infos = []
    for corpo in corpos_tabela:
        linhas_corpo = corpo.find_all('tr')
        for linha in linhas_corpo:
            info = {}
            a = linha.find('a')
            if a is not None:
                link = a['href']
                info[colunas[0]] = {"href": link, 'texto': a.text}
            else:
                th = linha.find('th')
                info[colunas[0]] = th.text
            tds = linha.find_all('td')
            for i, td in enumerate(tds):
                info[colunas[i+1]] = td.text
            infos.append(info)
    return infos

def pegar_tabela_escondida(response, id):
    soup = BeautifulSoup(response.text)
    comentarios_na_pagina = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comentario in comentarios_na_pagina:
        try:
            soup = BeautifulSoup(comentario, "html.parser")
            tabela = soup.find(attrs={"id": id})
            if tabela is not None:
                return pegar_linhas_tabela(comentario, id)
        except:
            pass

def pegar_html(url, path):
    sessao = requests.session()
    sessao.headers = HEADER
    sessao.headers["path"] = path
    response = sessao.get(url + path)
    sessao.close()
    return response

def main():
    URL = "https://www.basketball-reference.com"
    response = pegar_html(URL, "/teams/")
    tempo.sleep(2)
    infos_times = pegar_linhas_tabela(response.text, 'teams_active')
    infos = []
    for info_time in infos_times:
        try:
            endpoint = info_time['Franchise']['href']
            response = pegar_html(URL, endpoint)
            time = endpoint.split('/')[-2]
            tempo.sleep(2)
            infos_time = pegar_linhas_tabela(response.text, time)
            endpoint = infos_time[0]['Season']['href']
            response = pegar_html(URL, endpoint)
            tempo.sleep(2)
            per_game = pegar_linhas_tabela(response.text,'per_game')
            totals = pegar_linhas_tabela(response.text, 'totals')
            team_and_opponent = pegar_tabela_escondida(response, "team_and_opponent")
            team_misc = pegar_tabela_escondida(response, "team_misc")
            dict_time = {'time': time, 'totals': totals, 'per_game': per_game, 'team_misc': team_misc, 'team_and_opponent': team_and_opponent}
            infos.append(dict_time)
        except:
            pass

main()