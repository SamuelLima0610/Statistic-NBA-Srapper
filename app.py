import tkinter as tk
import queue
from tkinter import ttk
from functools import partial
from mining import Mining
from progress_of_task import ProgressOfTask


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('RPA for stats in basketball games (NBA)')
        self.q = queue.Queue()
        self.progress_of_task = ProgressOfTask()
        self.__prepare_progress_bar()
        self.__prepare_text_fields()
        self.__prepare_input_text_field()
        self.__prepare_buttons()
        self.tree = self.__create_table()
        handler = partial(self.__conclusion_of_interation_event, q=self.q, pb=self.pb)
        self.bind('<<Updated>>', handler)

    def __prepare_progress_bar(self):
        self.pb = ttk.Progressbar(
            self,
            orient='horizontal',
            mode='determinate',
            length=300,
            name='barra-progresso'
        )
        self.pb.grid(row=7, column=0, padx=10, pady=10, sticky='nswe', columnspan=3)

    def __prepare_text_fields(self):
        self.title_header = tk.Label(text=f"Initial Data", borderwidth=2, relief='solid')
        self.title_header.grid(row=0, column=0, padx=10, pady=10, sticky='nswe', columnspan=3)
        self.year_message = tk.Label(text="Season: ", anchor='e')
        self.year_message.grid(row=1, column=0, padx=10, pady=10, sticky='nswe', columnspan=2)
        self.stats = tk.Label(text="Progress of extraction", borderwidth=2, relief='solid')
        self.stats.grid(row=5, column=0, padx=10, pady=10, sticky='nswe', columnspan=3)
        self.progress_data = tk.Label(text=self.__update_progress(), name='info-progresso')
        self.progress_data.grid(row=6, column=0, padx=10, pady=10, sticky='nswe', columnspan=3)

    def __prepare_input_text_field(self):
        self.input_text_field = tk.Entry(font=('Arial', 10))
        self.input_text_field.grid(row=1, column=2, padx=10, pady=10, sticky='nsew')

    def __prepare_buttons(self):
        self.start_button = ttk.Button(
            self,
            text='Executar',
        )
        self.start_button['command'] = self.execute_task
        self.start_button.grid(column=2, row=4, padx=10, pady=10, sticky='nsew')

    def __conclusion_of_interation_event(self, event, q=None, pb=None):
        interation = q.get()
        self.progress_of_task.finish_a_interation(interation)
        pb['value'] = self.progress_of_task.get_porcentage()
        self.progress_data['text'] = self.__update_progress()

    def __update_progress(self):
        return self.progress_of_task.stats_of_progression()

    def __get_years(self):
        year_input = self.input_text_field.get()
        if year_input.count(',') > 0:
            years = year_input.split(',')
            list_of_years = [int(year) for year in years]
            return list_of_years
        return [int(year_input)]

    def execute_task(self):
        amount_of_games = 0
        lists_of_monthes = ['november', 'april', 'june', 'february', 'december', 'march', 'january'] # ['february', 'december'], [ 'march', 'january']
        threads = []
        years = self.__get_years()
        for i, month in enumerate(lists_of_monthes):
            thread = Mining([month], years, self, self.q, self.tree, i)
            threads.append(thread)
            amount_of_games += thread.calculate_the_amount_of_games()
        self.progress_of_task.set_total(amount_of_games)
        if self.progress_of_task.get_total() > 0:
            for thread in threads:
                thread.start()

    def __create_table(self):
        columns = ('id_thread', 'game', 'status')
        tree = ttk.Treeview(self, columns=columns, show='headings')
        tree.heading('id_thread', text='Id thread')
        tree.heading('game', text='Jogo')
        tree.heading('status', text='Status')
        tree.grid(row=9, column=0, padx=10, pady=10, sticky='nswe', columnspan=3)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=9, column=3, sticky='ns')
        return tree