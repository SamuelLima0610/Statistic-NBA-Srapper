from tkinter import messagebox

class ProgressOfTask:

    def __init__(self):
        self.total = 0
        self.done = 0
        self.porcentage = 0.0
        self.porcentage_by_game = 0
        self.time_prevision = 0
        
    def set_total(self, total):
        self.total = total
        if total == 0:
            self.porcentage_by_game = 0
            messagebox.showinfo(title="Sem dados", message="Nenhum dado a ser processado!")
        else:
            self.porcentage_by_game = (1 / total) * 100

    def get_total(self):
        return self.total

    def get_porcentage(self):
        return self.porcentage

    def finish_a_interation(self, interation_time):
        self.done += 1
        undone_interations = self.total - self.done
        self.porcentage += self.porcentage_by_game
        self.time_prevision = (undone_interations * interation_time) / 3
        if undone_interations == 0:
            self.porcentage = 100.0
            self.time_prevision = 0
            messagebox.showinfo(title="Finalizado",
                                message="Finalizado com sucesso!")

    def stats_of_progression(self):
        prevision_time = f'{self.time_prevision}s'
        if self.time_prevision > 60:
            time_in_minutes = self.time_prevision / 60
            prevision_time = f'{time_in_minutes:.2f} min'
        undone_interations = self.total - self.done
        return f'Progresso atual: {self.porcentage:.2f}%' \
               f'[Realizadas: {self.done} | ' \
               f'Falta: {undone_interations} ' \
               f'| Tempo de conclusão: {prevision_time}]'
