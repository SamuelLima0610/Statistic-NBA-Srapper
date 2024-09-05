import psycopg2, os
from dotenv import load_dotenv
load_dotenv()


class BancoDeDados:

    def __init__(self):
        self.conn = psycopg2.connect(database=os.environ['NOME'],
                                host=os.environ['HOST_BANCO'],
                                user=os.environ['USUARIO_BANCO'],
                                password=os.environ['SENHA'],
                                port=os.environ['PORT_BANCO'])
        self.cursor = self.conn.cursor()

    def insert(self, query):
        try:
            self.cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

    def search(self, query, quantity=None):
        try:
            self.cursor.execute(query)
            if quantity is None:
                return self.cursor.fetchall()
            elif quantity > 1:
                return self.cursor.fetchmany(size=quantity)
            else:
                return self.cursor.fetchone()
        except Exception as e:
            print(e)

    def fechar(self):
        self.cursor.close()
        self.conn.close()