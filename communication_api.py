import requests, os
from dotenv import load_dotenv

load_dotenv()

class Api:

    def __init__(self):
        self.urlApi = os.environ['API']

    def send_request(self, method, endpoint, object_json=None):
        url = f'{self.urlApi}{endpoint}'
        data = {}
        for key, value in object_json.items():
            data[key.lower()] = value
        if method == 'POST':
            r = requests.request(method, url, json=data, verify=False)
        else:
            r = requests.request(method, url, verify=False)
        if r.status_code == 404:
            raise Exception("Error 404")
        elif r.status_code == 409:
            raise Exception("Error 409")
        elif r.status_code > 300:
            raise Exception("Processo não pesquisado anteriormente")
        return r.json()