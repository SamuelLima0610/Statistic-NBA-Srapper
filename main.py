import requests
from header import HEADER
from bs4 import BeautifulSoup, Comment


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
    placeholders = soup.find_all(string=lambda text: isinstance(text, Comment))
    tabelas_ids = ["team_and_opponent",]
    for placeholder in placeholders:
        try:
            soup = BeautifulSoup(placeholder, "html.parser")
            ids = [table['id'] for table in soup.find_all('table')]
            print(ids)
            tabela = soup.find(attrs={"id": id})
            if tabela is not None:
                return pegar_linhas_tabela(placeholder, id)
        except:
            pass

def get_html(url, path):
    session = requests.session()
    session.headers = HEADER
    session.headers["path"] = path
    response = session.get(url + path)
    return response

def main():
    URL = "https://www.basketball-reference.com"
    response = get_html(URL, "/teams/")
    infos_times = pegar_linhas_tabela(response.text, 'teams_active')
    endpoint = infos_times[0]['Franchise']['href']
    response = get_html(URL, endpoint)
    infos_time = pegar_linhas_tabela(response.text, endpoint.split('/')[-2])
    endpoint = infos_time[0]['Season']['href']
    response = get_html(URL, endpoint)
    per_game = pegar_linhas_tabela(response.text,'per_game')
    totals = pegar_linhas_tabela(response.text, 'totals')
    team_and_opponent = pegar_tabela_escondida(response, "team_and_opponent")
    team_misc = pegar_tabela_escondida(response, "team_misc")
    injuries = pegar_tabela_escondida(response, "injuries")
    print(totals)

main()