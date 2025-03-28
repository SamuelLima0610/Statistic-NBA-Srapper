import requests, os
from dotenv import load_dotenv
from exception import Erro404

load_dotenv()

class Api:

    def __init__(self):
        self.urlApi = os.environ['API']

    def send_request(self, method, endpoint, object_json=None):
        url = f'{self.urlApi}{endpoint}'
        data = {}
        if method == 'POST':
            for key, value in object_json.items():
                data[key.lower()] = value
            r = requests.request(method, url, json=data, verify=False)
        else:
            r = requests.request(method, url, verify=False)
        if r.status_code == 404:
            raise Erro404("Error 404")
        elif r.status_code == 409:
            raise Exception("Error 409")
        elif r.status_code > 300:
            print(r)
            raise Exception("Processo não pesquisado anteriormente")
        return r.json()