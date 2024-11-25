import requests
from header import HEADER
from bs4 import BeautifulSoup, Comment
from constants import GAME_COLUMNS


class ProcessadorSite:

    def get_info_from_table(self, text, tabel_id, dont_get=[]):
        soup = BeautifulSoup(text)
        tabel = soup.find(attrs={"id": tabel_id})
        header_table = tabel.find('thead')
        header_columns = header_table.find_all('th')
        columns = [column.text for column in header_columns if column.text not in dont_get]
        tabel_body = tabel.find_all('tbody')
        infos = []
        for body in tabel_body:
            trs = body.find_all('tr')
            for tr in trs:
                info = {}
                a = tr.find('a')
                if a is not None:
                    link = a['href']
                    if columns[0] in ['Starters', 'Reserves']:
                        columns[0] = 'Player'
                    info[columns[0]] = {"href": link, 'text': a.text}
                else:
                    th = tr.find('th')
                    info[columns[0]] = th.text
                tds = tr.find_all('td')
                for i, td in enumerate(tds):
                    info = td.text
                    column = columns[i+1]
                    if info == '':
                        continue
                    if info == 'Box Score':
                        a = td.find('a')
                        info = a['href']
                        column = 'Box Score'
                    elif columns[i+1] in GAME_COLUMNS.keys():
                        column = GAME_COLUMNS[columns[i+1]]
                    else:
                        informacao = td.text
                        column = columns[i+1]
                    info[column] = informacao
                infos.append(info)
        return infos

    def get_info_from_table_commented(self, text, id):
        soup = BeautifulSoup(text)
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            try:
                soup = BeautifulSoup(comment, "html.parser")
                tabel = soup.find(attrs={"id": id})
                if tabel is not None:
                    return self.get_info_from_table(comment, id)
            except:
                pass

    def get_html(self, url, path):
        session = requests.session()
        session.headers = HEADER
        session.headers["path"] = path
        response = session.get(url + path)
        session.close()
        return response
    
    def get_element_by_class(self, text, tag, classe):
        soup = BeautifulSoup(text)
        element = soup.find(tag, {'class':classe})
        return element
        
    def get_scorebox_from_team(self, element, is_home_team):
        if is_home_team:
            team = element.find_all('strong')[0]
        else:
            team = element.find_all('strong')[1]
        team = team.text
        return team.replace('\n','')
    
    def get_scorebox(self, elemento, is_home_team):
        if is_home_team:
            scorebox = elemento.find_all('div', {'class': 'score'})[0]
        else:
            scorebox = elemento.find_all('div', {'class': 'score'})[1]
        scorebox = scorebox.text
        return scorebox.replace('\n','')