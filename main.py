from mining import Atividade

def main():
    lists_of_monthes = [['november', 'april', 'june'], ['february', 'december'], [ 'march', 'january']]
    threads = []
    for list_of_monthes in lists_of_monthes:
        thread = Atividade(list_of_monthes)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
main()