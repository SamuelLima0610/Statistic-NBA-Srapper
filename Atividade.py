from threading import Thread
import time
from time import perf_counter
from calculadora import CalculadoraRCB
import os
from download_arquivos import GerenciadorArquivos
from excecoes.excecoes import MunicipioNaoExiste, SelectErro, ErroNaoPreencheu, ErroValorInconsistente
from cidades import cidades


class Atividade(Thread):

    def __juntar_informacoes(self, dict_1, dict_2):
        result = dict_1 | dict_2
        return result

    def __init__(self, lista, r, q, tabela, id_da_thread, escritor_excel, id_tarefa):
        super().__init__()
        self.contratos = lista
        self.r = r
        self.q = q
        self.tabela = tabela
        self.id_da_thread = id_da_thread
        self.escritor_excel = escritor_excel
        self.padrao = None
        self.ultima_url = ''
        self.id_tarefa = id_tarefa


    def _realizar_processo_login(self, executar):
        try:
            time.sleep(5)
            executar.login()
            executar.resolucaoCaptcha()
        except:
            executar.fechar_pagina()
    
    def __escrever_no_excel(self, status, mensagem_status, index):
        self.contratos[index]['Status'] = status
        self.contratos[index]['Codigo Controle Calculadora'] = mensagem_status
        self.escritor_excel.escrever_no_arquivo_excel(self.contratos[index], self.contratos[index]['linha'])

    def __verificar_cidades_erradas(self, cidade):
        if cidade in cidades.keys():
            return cidades[cidade]
        else:
            return cidade

    def __preparar_mensagem_de_erro(self, codigo_retorno):    
        mensagem = ''
        if codigo_retorno == 1:
            mensagem = "Erro muncipio"
        elif codigo_retorno == 2:
            mensagem = "Erro no preenchimento de debitos"
        elif codigo_retorno == 7:
            mensagem = "Erro: inconsistência no valores de debitos"
        elif codigo_retorno == 3:
            mensagem == "Erro na cor"
        elif codigo_retorno == 4:
            mensagem = "Erro: Dados incorretos marca, modelo, ano fab e mod"
        elif codigo_retorno == 6:
            mensagem = "Erro: Em avaria, restrições"
        else:
            mensagem = 'Erro no salvamento da calculadora'
        return mensagem

    def __preparar_estado_calculadora(self, codigo_calculadora):
        mensagem = ''
        if "NAO HABILITADO" in codigo_calculadora and "Popup:(" in codigo_calculadora:
            self.status_execucao = -1
            mensagem = 'Não habilitada (Já inserido)'
        elif "NAO" in codigo_calculadora and "Popup:(" not in codigo_calculadora:
            self.status_execucao = 1
            mensagem = 'Calculadora Negativa'
        elif "APREENDER" in codigo_calculadora or "RECEBER" in codigo_calculadora:
            self.status_execucao = 1
            mensagem = 'Calculadora Positiva'
        elif "Popup:(" in codigo_calculadora:
            self.status_execucao = -1
            mensagem = 'Erro'
        return mensagem

    def __conclusao_processo(self, index, ajuizamento, executar):
        if not ajuizamento:
            executar.concluir(self.contratos[index], ajuizamento, self.id_tarefa)
            return False
        else:
            codigo_calculadora = executar.concluir(self.contratos[index], True, self.id_tarefa)
            self.contratos[index]['Status'] = self.__preparar_estado_calculadora(codigo_calculadora)
            self.contratos[index]['Codigo Controle Calculadora'] = codigo_calculadora
            self.escritor_excel.escrever_no_arquivo_excel(self.contratos[index], self.contratos[index]['linha'])
            self.status[index] = 'S'                        
            executar.recarregar_pagina()
            return True
    
    def atualizar_interface(self, inicio, fim, contrato, status):
        tempo = fim - inicio
        self.q.put({"tempo": tempo, "status": self.status_execucao, 'contrato': contrato})
        self.r.event_generate('<<Updated>>', when='tail')
        self.tabela.insert('', 0, values=(self.id_da_thread, contrato, status))

    def preencher_form(self, executar, contrato, e_ajuizamento, info_banco_dados):
        try:
            fipe_ok = executar.verificar_fipe(contrato)
            if not fipe_ok:
                return 4
        except:
            return 4
        try:
            executar.locacao_remocao(contrato, e_ajuizamento, info_banco_dados)
        except MunicipioNaoExiste:
            return 1
        except SelectErro:
            return 5
        try:
            executar.desmarcar_outras_opcoes_restricoes()
            executar.parte_restricoes(contrato)
            executar.avaria()
            executar.causa(e_ajuizamento)
        except:
            return 6
        try:
            executar.debitos(contrato)
        except ErroNaoPreencheu:
            return 2
        except ErroValorInconsistente:
            return 7
        try:
            executar.lancamentos_adicionais(contrato, e_ajuizamento)
        except:
            return 3
        return 0

    def run(self):
        self.status = ["N" if 'Status' not in contrato.keys() else 'S' for contrato in self.contratos]
        if self.status.count("N") > 0: 
            while True:
                executar = CalculadoraRCB()
                self._realizar_processo_login(executar)
                for index in range(len(self.contratos)):
                    if self.status[index] == 'N':
                        try:
                            executar.menuCalculadora()
                            start_time = perf_counter()
                            resposta = executar.pesquisa_contrato(self.contratos[index]['Contrato'])
                            if resposta != 'Ok':
                                self.status_execucao = -1
                                end_time = perf_counter()
                                self.contratos[index]['Status'] = 'Contrato bloqueado'
                                self.contratos[index]['Codigo Controle Calculadora'] = resposta
                                self.escritor_excel.escrever_no_arquivo_excel(self.contratos[index], self.contratos[index]['linha'])
                                self.status[index] = 'S'
                                self.atualizar_interface(start_time, end_time, self.contratos[index]['Contrato'], "Erro")
                                continue
                            time.sleep(2)
                            tipo_calculo  = executar.selecionar_tipo_de_calculo()
                            self.contratos[index]['Cor'] = executar.consulta_banco_dados_cor(self.contratos[index]['Contrato'])
                            info_responsavel = executar.consulta_banco_dados(self.contratos[index]['Contrato'])
                            info_responsavel['municipio'] = self.__verificar_cidades_erradas(info_responsavel['municipio'].upper())
                            self.contratos[index]['Municipio'] = info_responsavel['municipio']
                            #input(self.contratos[index]['Municipio'])
                            ajuizamento = False if tipo_calculo == 0 else True
                            try:
                                executar.selecionar_calculo(tipo_calculo)
                            except:
                                self.status_execucao = -1
                                self.contratos[index]['Status'] = 'Contrato bloqueado'
                                self.contratos[index]['Codigo Controle Calculadora'] = 'Não permite realizar o modelo de ajuizamento ou atualização'
                                self.escritor_excel.escrever_no_arquivo_excel(self.contratos[index], self.contratos[index]['linha'])
                                self.status[index] = 'S'
                                self.atualizar_interface(start_time, end_time, self.contratos[index]['Contrato'], "Erro")
                            codigo_retorno = self.preencher_form(executar, self.contratos[index], ajuizamento, info_responsavel)
                            if codigo_retorno != 0:
                                if codigo_retorno == 5:
                                    break
                                self.status_execucao = -1
                                mensagem = self.__preparar_mensagem_de_erro(codigo_retorno)
                                self.__escrever_no_excel('Erro', mensagem, index)
                                self.status[index] = 'S'
                                executar.recarregar_pagina()
                                end_time = perf_counter()    
                                self.atualizar_interface(start_time, end_time, self.contratos[index]['Contrato'], "Erro")                       
                                continue
                            finalizou = self.__conclusao_processo(index, ajuizamento, executar)
                            end_time = perf_counter()        
                            if finalizou:
                                self.atualizar_interface(start_time, end_time, self.contratos[index]['Contrato'], "Sucesso")                  
                        except:
                            executar.recarregar_pagina()
                if self.status.count('S') == len(self.status):
                    break
                executar.finalizar()
        dir_download = rf'{os.getcwd()}\CALCULADORA'
        files = os.listdir(dir_download)
        files_names = [file.split('.')[0] for file in files]
        for calculo in self.contratos:
            if "Calculadora" in calculo["Status"] and str(calculo['Contrato']) in files_names:
                try:
                    GerenciadorArquivos.download_arquivos(calculo, self.id_tarefa, self.id_da_thread)
                    GerenciadorArquivos.passar_arquivo(calculo['Contrato'], self.id_tarefa)
                except:
                    continue