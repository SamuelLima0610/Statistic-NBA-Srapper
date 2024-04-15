from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

load_dotenv()

class Mongo:

    def __init__(self):
        URI = f"mongodb+srv://samvlima10:{quote_plus(os.environ['PASSWORD'])}@nba.fdxxtki.mongodb.net/"
        # Create a new client and connect to the server
        self.cliente = MongoClient(URI, server_api=ServerApi('1'))
        # Send a ping to confirm a successful connection
        self.banco_de_dados = self.cliente["NBA"]

    def inserir(self, colecao, info):
        try:
            ref_colecao = self.banco_de_dados[colecao]
            ref_colecao.insert_one(info)
        except Exception as e:
            print(e)

    def atualizar(self, colecao, info, time):
        try:
            ref_colecao = self.banco_de_dados[colecao]
            ref_colecao.update_one({'team': time}, { "$set": { "info": info } })
        except Exception as e:
            print(e)

    def existe_informacao(self, colecao, time):
        try:
            result = self.banco_de_dados[colecao].find_one({'team': time})
            if result is None:
                return False
            return True
        except Exception as e:
            return False
        
    def fechar_banco(self):
        self.cliente.close()