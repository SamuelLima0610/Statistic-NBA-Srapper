import requests
from header import HEADER
from bs4 import BeautifulSoup, Comment


class ProcessadorSite:

    def pegar_linhas_tabela(self, text, id_tabela):
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

    def pegar_tabela_escondida(self, text, id):
        soup = BeautifulSoup(text)
        comentarios_na_pagina = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comentario in comentarios_na_pagina:
            try:
                soup = BeautifulSoup(comentario, "html.parser")
                tabela = soup.find(attrs={"id": id})
                if tabela is not None:
                    return pegar_linhas_tabela(comentario, id)
            except:
                pass

    def pegar_html(self, url, path):
        sessao = requests.session()
        sessao.headers = HEADER
        sessao.headers["path"] = path
        response = sessao.get(url + path)
        sessao.close()
        return response