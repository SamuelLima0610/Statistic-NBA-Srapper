from atividade import Atividade

def main():
    meses = [['november', 'april', 'june'], ['february', 'december'], [ 'march', 'january']]
    atividades = []
    for lista_mes in meses:
        atividade = Atividade(lista_mes)
        atividade.start()
        atividades.append(atividade)
    for atividade in atividades:
        atividade.join()
main()