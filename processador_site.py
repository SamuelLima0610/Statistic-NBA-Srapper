import requests
from header import HEADER
from bs4 import BeautifulSoup, Comment


class ProcessadorSite:

    def pegar_linhas_tabela(self, text, id_tabela, chaves_a_serem_desconsideradas=[]):
        soup = BeautifulSoup(text)
        tabela = soup.find(attrs={"id": id_tabela})
        cabecalho = tabela.find('thead')
        colunas_cabecalho = cabecalho.find_all('th')
        colunas = [coluna.text for coluna in colunas_cabecalho if coluna.text not in chaves_a_serem_desconsideradas]
        corpos_tabela = tabela.find_all('tbody')
        infos = []
        for corpo in corpos_tabela:
            linhas_corpo = corpo.find_all('tr')
            for linha in linhas_corpo:
                info = {}
                a = linha.find('a')
                if a is not None:
                    link = a['href']
                    if colunas[0] in ['Starters', 'Reserves']:
                        colunas[0] = 'Player'
                    info[colunas[0]] = {"href": link, 'texto': a.text}
                else:
                    th = linha.find('th')
                    info[colunas[0]] = th.text
                tds = linha.find_all('td')
                for i, td in enumerate(tds):
                    informacao = td.text
                    coluna = colunas[i+1]
                    if informacao == '':
                        continue
                    if informacao == 'Box Score':
                        a = td.find('a')
                        informacao = a['href']
                        coluna = 'Box Score'
                    else:
                        informacao = td.text
                        coluna = colunas[i+1]
                    info[coluna] = informacao
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
                    return self.pegar_linhas_tabela(comentario, id)
            except:
                pass

    def pegar_html(self, url, path):
        sessao = requests.session()
        sessao.headers = HEADER
        sessao.headers["path"] = path
        response = sessao.get(url + path)
        sessao.close()
        return response
    
    def pegar_elemento_por_classe(self, text, tag, classe):
        soup = BeautifulSoup(text)
        elemento = soup.find(tag, {'class':classe})
        return elemento
        
    def pegar_time_no_scorebox(self, elemento, time_da_casa):
        if time_da_casa:
            time = elemento.find_all('strong')[0]
        else:
            time = elemento.find_all('strong')[1]
        time = time.text
        return time.replace('\n','')
    
    def pegar_pontuacao_no_scorebox(self, elemento, time_da_casa):
        if time_da_casa:
            pontuacao = elemento.find_all('div', {'class': 'score'})[0]
        else:
            pontuacao = elemento.find_all('div', {'class': 'score'})[1]
        pontuacao = pontuacao.text
        return pontuacao.replace('\n','')