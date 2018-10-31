import threading


class ThreadVC(threading.Thread):
    """Classe que executa a thread de processamento da imagem"""

    def __init__(self, thread_id, name, imagem):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.imagem = imagem

    def run(self):
        print("Starting " + self.name)
        print('1')
        self.imagem.aplicarYolo()  # nao esquecer de apagar o arquivo antes de reescrever
        print('2')
        self.imagem.ObterBoundingBox()
        numero = self.imagem.ContarPessoas()
        print("NUMERO DE PESSOAS--------------" + str(numero))
        self.imagem.OrganizarBoundingBoxes()
        self.imagem.ClassificarBoundingBox()
        self.imagem.GerarFotos()
        self.imagem.BoundingBoxApproach()

        print("Exiting " + self.name)