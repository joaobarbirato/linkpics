# bibliotecas do python
# from __future__ import print_function
import os
import random
import shutil

from app.align_module import models
from app.src.PLN.get_syns import get_syns
from app.src.PLN.m_PLN import (AplicadorPLN, get_word_from_lemma, has_mwe, belongs_to_mwe)
from app.src.PLN.text_process import ThreadPLN
from app.src.PLN.word_embeddings import WordEmbeding
from app.src.UTIL import utils
from app.src.VC.image_process import ThreadVC
from app.src.VC.imagem import Imagem
from app.align_module.models import AlignmentGroup, Alignment
from app.src.align.align_objects import AlignObjects
from app.src.align.align_persons import AlignPersons
from config import STATIC_REL, SRC_DIR


class ColorPalette:
    def __init__(self):
        self.colors_bounding_box = [(0, 0, 255),
                                    (139, 0, 0),
                                    (154, 205, 50),
                                    (0, 255, 255),
                                    (0, 0, 0),
                                    (0, 165, 255),
                                    (0, 0, 255),
                                    (255, 191, 0),
                                    (144, 238, 144)]
        self.colors_html = [(255, 0, 0),
                            (0, 0, 139),
                            (50, 205, 154),
                            (255, 255, 0),
                            (0, 0, 0),
                            (255, 165, 0),
                            (255, 0, 0),
                            (0, 191, 255),
                            (144, 238, 144)]
        self.index = 0

    def get_curr_color(self, type="html"):
        return self.colors_html[self.index] if type == "html" else self.colors_bounding_box[self.index]

    def inc_index(self):
        self.index += 1

    def set_index(self, new_index):
        self.index = new_index

    def next_color(self, type="html", inc=False):
        if self.index > len(self.colors_html) - 1:
            # create random different color
            red = 255
            green = 0
            blue = 0
            while (red, green, blue) in self.colors_html:
                red = random.randint(0, 255)
                green = random.randint(0, 255)
                blue = random.randint(0, 255)
            # append to both lists
            self.colors_html.append((red, green, blue))
            self.colors_bounding_box.append((blue, green, red))

        return_color = None
        if type == "html":
            return_color = self.colors_html[self.index]
        elif type == "bb":
            return_color = self.colors_bounding_box[self.index]

        if inc:
            self.inc_index()

        return return_color

    def reset_colors(self):
        self.index = 0


class AlignTool:
    def __init__(self, crawler=None):
        if crawler:
            self.w_embeddings = WordEmbeding(100)  # inicializa as word embeddings
            self.PATH_PROJETO = os.path.dirname(os.path.abspath(__file__)) + "/../../../"
            self.crawler = crawler()
            self.legenda = ""
            self.titulo_noticia = ""
            self.noticia = ""
            self.titulo_diretorio = ""
            self.path_imagem = ""
            self.path_legenda = ""
            self.path_noticia = ""
            self.path_titulo = ""
            self.directory = ""
            self.nome_arquivo = ""
            self.lst_legenda = []
            self.lst_top_nomeadas_texto = []
            self.list_boundingBoxOrganizada = []
            self.lst_top_substantivos_objects = []
            self.dict_lematizado = {}
            self.noticia_sem_imagem = False
            self.total_pessoas = 0
            self.total_nomes = 0

            self.index_cor_bounding_box = 0
            # Red, Blue , Dark Green, Yellow, Black, Orange, Light Blue, Light Green
            self.colors_bounding_box = [(0, 0, 255),
                                        (139, 0, 0),
                                        (154, 205, 50),
                                        (0, 255, 255),
                                        (0, 0, 0),
                                        (0, 165, 255),
                                        (0, 0, 255),
                                        (255, 191, 0),
                                        (144, 238, 144)]

            self.colors_html = [(255, 0, 0),
                                (0, 0, 139),
                                (50, 205, 154),
                                (255, 255, 0),
                                (0, 0, 0),
                                (255, 165, 0),
                                (255, 0, 0),
                                (0, 191, 255),
                                (144, 238, 144)]

            self.orig_legenda = ""
            self.orig_titulo = ""
            self.orig_texto = ""
            self.group = None
            self.palette = ColorPalette()

    def _remover_caracteres_especiais(self, titulo_noticia):
        """Remove caracteres estranhos das noticias"""
        titulo_noticia = titulo_noticia.replace('"', "")
        titulo_noticia = titulo_noticia.replace(",", "")
        titulo_noticia = titulo_noticia.replace("\n", "")
        titulo_noticia = titulo_noticia.replace("'", "")
        titulo_noticia = titulo_noticia.replace("$", "")
        return titulo_noticia

    def _limpar_arquivos(self, noticia, imagem):
        os.remove(noticia)
        os.remove(SRC_DIR + "noticia_atual/img_original.jpg")
        os.remove(SRC_DIR + "noticia_atual/noticia.txt")
        os.remove(SRC_DIR + "noticia_atual/titulo.txt")

    def _text_contains(self, substring=None):
        return self.titulo_noticia.find(substring) >= 0 or self.noticia.find(substring) >= 0 or self.legenda.find(substring)

    def _get_resources(self, url):
        # rastreia a página
        self.nome_arquivo, self.titulo_noticia, encontrou_img = self.crawler.crawl_page(url)
        print("aq")
        if encontrou_img == 1 and os.path.exists(self.nome_arquivo):  # se achou imagem na notícia
            if self.titulo_noticia != "":  # se a noticia existe em ingles
                # le o arquivo e guarda na variavel
                self.noticia = file_to_variavel(self.nome_arquivo)
                self.noticia = self.noticia.replace(".", ". ")
                self.noticia = self.noticia.replace(". . . ", "... ")
                self.noticia = self.noticia.replace(",", ", ")
                self.noticia = self.noticia.replace("  ", " ")

                # Remove caracteres estranhos das noticias
                self.titulo_noticia = self._remover_caracteres_especiais(self.titulo_noticia)
                self.titulo_noticia = self.titulo_noticia.replace(".", ". ")
                self.titulo_noticia = self.titulo_noticia.replace(". . . ", "... ")
                self.titulo_noticia = self.titulo_noticia.replace(",", ", ")
                self.titulo_noticia = self.titulo_noticia.replace("  ", " ")

                self.titulo_diretorio = self.titulo_noticia.replace(" ", "")  # titulo do diretorio
                self.titulo_diretorio = self.titulo_diretorio.replace("?", "")  # titulo do diretorio
                self.titulo_diretorio = self.titulo_diretorio.replace(":", "")  # titulo do diretorio
                # grava no txt o titulo - noticias/nomenoticia/titulo.txt
                utils.escrever_arquivo(self.titulo_noticia, SRC_DIR + "noticia_atual/titulo.txt")

                # grava  a legenda da imagem--noticias/nomenoticia/caption.txt
                if os.path.exists(self.nome_arquivo + "_caption.txt"):
                    self.legenda = file_to_variavel(self.nome_arquivo + "_caption.txt")
                    self.legenda = self.legenda.replace("\n", "")
                    self.legenda = self.legenda.replace(".", ". ")
                    self.legenda = self.legenda.replace(". . . ", "... ")
                    self.legenda = self.legenda.replace(",", ", ")
                    self.legenda = self.legenda.replace("  ", " ")
                    self.path_legenda = self.nome_arquivo + "_caption.txt"  # caminho da legenda
                else:
                    self.legenda = ""
                    self.path_legenda = ""

                self.path_imagem = self.nome_arquivo + ".jpg"  # caminho da imagem original
                shutil.copy2(self.path_imagem, STATIC_REL + '/alinhamento2.jpg')
                print("imagem copiada")

                self.path_titulo = SRC_DIR + "noticia_atual/titulo.txt"  # caminho do título

                self.path_noticia = self.nome_arquivo  # path da noticia

                self.directory = "noticias/" + self.titulo_diretorio  # nome do diretorio que será criado

                if not os.path.exists(self.directory):  # se a noticia ainda não foi coletada
                    os.makedirs(self.directory)  # cria o diretorio da noticia
                    # envia a imagem original para o dir da noticia
                    os.rename(self.path_imagem, self.directory + "/img_original.jpg")
                    # envia a  noticia original para o dir da noticia
                    os.rename(self.nome_arquivo, self.directory + "/noticia.txt")
                    # envia a  legenda  para o dir da noticia
                    if os.path.exists(self.nome_arquivo + "_caption.txt"):
                        os.rename(self.path_legenda, self.directory + "/caption.txt")
                    # envia o titulo para o dir da noticia
                    os.rename(self.path_titulo, self.directory + "/titulo.txt")
                    # novo path da imagem original
                    self.path_imagem = self.directory + "/img_original.jpg"
                    self.path_noticia = self.directory + "/noticia.txt"  # novo path da noticia
            else:  # Se a noticia não estiver em inglês
                os.remove(self.nome_arquivo + ".jpg")
                if os.path.exists(self.nome_arquivo + "_caption.txt"):
                    os.remove(self.nome_arquivo + "_caption.txt")

            self.orig_legenda = self.legenda
            self.orig_titulo = self.titulo_noticia
            self.orig_texto = self.noticia
        else:
            self.noticia_sem_imagem = True

    def _set_manual_resources(self):
        self.titulo_diretorio = self.titulo_noticia.replace(" ", "")  # titulo do diretorio
        # grava no txt o titulo - noticias/nomenoticia/titulo.txt
        utils.escrever_arquivo(self.titulo_noticia, SRC_DIR + "noticia_atual/titulo.txt")

        shutil.copy2(self.path_imagem, STATIC_REL + '/alinhamento2.jpg')
        print("imagem copiada")

        self.directory = SRC_DIR + "noticias/" + self.titulo_diretorio  # nome do diretorio que será criado
        utils.escrever_arquivo(self.noticia, SRC_DIR + "noticia_manual.txt")
        self.path_noticia = SRC_DIR + "noticia_manual.txt"  # path da noticia
        # if os.path.exists(self.directory):  # se a noticia ainda não foi coletada
        #             shutil.rmtree(self.directory)
        if not os.path.exists(self.directory):  # se a noticia ainda não foi coletada
            os.makedirs(self.directory)  # cria o diretorio da noticia
        shutil.copy2(self.path_imagem, self.directory + "/img_original.jpg")

    """
        Procedimento para marcar as palavras alinhadas no texto
    """

    def _show_align_text(self, persons_aligned=None, object_aligned=None):
        retorno = [None, None]
        if persons_aligned:
            for key, value in persons_aligned.items():
                nomes = key.split(' ')
                for nome in nomes:
                    alinhamento = self.group.get_alignment(term=nome)
                    self._paint_text(nome, alinhamento)
                self.palette.inc_index()
            retorno[0] = persons_aligned

        if object_aligned:
            for key, value in object_aligned.items():
                print("Key: ", key, "\nValue: ", value)
                palavra = get_word_from_lemma(lemma=key.split("#")[0])
                index = 0 if len(key.split("#")) == 1 else key.split("#")[1]
                alinhamento = self.group.get_alignment(term=key.split("#")[0], index=int(index))
                lst_mwe = belongs_to_mwe(word=palavra)

                if has_mwe() and lst_mwe is not False:
                    for mwe in lst_mwe:
                        if self._text_contains(mwe):  # a detecção de MWEs ignora pontuação no texto
                            alinhamento.add_mwe(mwe=mwe)
                            self._paint_text(mwe, alinhamento)

                palavras = self._word_to_wordpoint(palavra)
                for p in palavras:
                    if self._text_contains(p):
                        self._paint_text(p, alinhamento)

                # n:1
                palavra_syns = get_syns(palavra)
                if palavra_syns is not None:
                    for ps in palavra_syns:
                        palavras_syns_points = self._word_to_wordpoint(
                            ps if get_word_from_lemma(ps) is None else get_word_from_lemma(ps)
                        )
                        for p in palavras_syns_points:
                            if self._text_contains(p):
                                self._paint_text(p, alinhamento)

                        alinhamento.add_syn(syn=ps)

                self.palette.inc_index()

            retorno[1] = object_aligned

        return retorno

    @staticmethod
    def _word_to_wordpoint(palavra):
        return [
            palavra + ".", palavra + "?", palavra + "!", palavra + ";", palavra + "'",
            palavra.title() + ".", palavra.title() + " ", palavra.title() + "?", palavra.title() + "!",
            palavra.title() + ";", palavra.title() + ",", palavra.title() + "'",
            palavra.lower() + " ", palavra.lower() + ".", palavra.lower() + "?", palavra.lower() + "!",
            palavra.lower() + ";", palavra.lower() + ",", palavra.lower() + "'",
            palavra.upper() + " ", palavra.upper() + ".", palavra.upper() + "?", palavra.upper() + "!",
            palavra.upper() + ";", palavra.upper() + ",", palavra.upper() + "'"
        ]

    def _paint_text(self, p, alinhamento=None):
        if not alinhamento.has_color():
            color = self.palette.get_curr_color(type="html")
            print("\tPAINTING TEXT FOR ", p, " WITH ", color)
            alinhamento.add_color(color)

        _open_tag = '<b style="color:rgb(' + str(alinhamento.get_color()) + ');">'
        _close_tag = '</b>'
        _pre_char_list = ['(', ' ']
        for pre_char in _pre_char_list:
            self.noticia = self.noticia.replace(pre_char + p, pre_char + _open_tag + p + _close_tag)
            self.legenda = self.legenda.replace(pre_char + p, pre_char + _open_tag + p + _close_tag)
            self.titulo_noticia = self.titulo_noticia.replace(' ' + p, _open_tag + p + _close_tag)

    def _process_text_image(self):
        # cria uma instancia da classe Imagem, passando o path da imagem
        print(self.directory)
        print(self.path_noticia)
        imagem = Imagem(self.path_imagem, self.directory, self.PATH_PROJETO)
        # cria uma instancia do processador de texto
        aplicador_pln = AplicadorPLN(self.PATH_PROJETO, self.noticia, self.legenda, self.titulo_noticia,
                                     self.path_noticia, self.directory, self.w_embeddings)

        self.lst_top_nomeadas_texto = aplicador_pln.get_list_top_entidades_nomeadas()

        print("[BEFORE]Pessoas no texto:" + str(len(self.lst_top_nomeadas_texto)))
        #####CRIA AS THREADS DE PLN E VC#####
        threads = []
        thread_pln = ThreadPLN(1, "PLN", aplicador_pln)
        thread_vc = ThreadVC(2, "VC", imagem)

        # Inicializa as threads
        thread_pln.start()
        thread_vc.start()

        threads.append(thread_pln)
        threads.append(thread_vc)
        # Espera as threads terminarem
        for t in threads:
            t.join()

        ##########################################
        # Alinhar as pessoas
        self.lst_legenda = aplicador_pln.entidades_legenda()

        self.lst_top_nomeadas_texto = aplicador_pln.get_list_top_entidades_nomeadas()
        print("Pessoas no texto:",  [ne.palavra for ne in self.lst_top_nomeadas_texto])#str(len(self.lst_top_nomeadas_texto)))
        self.dict_lematizado = aplicador_pln.get_dict_lematizado()
        self.list_boundingBoxOrganizada = imagem.list_boundingBoxOrganizada
        self.lst_top_substantivos_objects = aplicador_pln.lst_top_substantivos_objects
        print("--------------SUBSTANTIVOS-------------")
        print(self.lst_top_substantivos_objects)

    def align_from_url(self, url, person_choose, object_choose):
        """Alinha a partir de uma url fornecida pela usuario"""
        try:
            self.noticia_sem_imagem = False
            self._get_resources(url)

            if self.noticia_sem_imagem is True:
                return 0

            self._process_text_image()

            pessoas_noticia = len(self._get_bounding_persons(self.list_boundingBoxOrganizada))
            nomes_noticia = len(self.lst_top_nomeadas_texto)

            self.total_pessoas += pessoas_noticia
            self.total_nomes += nomes_noticia

        except Exception as e:
            print(e)

        self.group = AlignmentGroup(name="align_tool")
        # Alinha as pessoas
        person = AlignPersons(self.lst_legenda, self.lst_top_nomeadas_texto, self.list_boundingBoxOrganizada,
                              self.directory + "/img_original.jpg", self.directory + "/", self.index_cor_bounding_box,
                              self.colors_bounding_box, align_group=self.group, palette=self.palette)
        persons_aligned, self.group = person.align(person_choose)

        if persons_aligned is None:
            persons_aligned = {}

        # O indice das cores continua de onde parou o indice realizado no alinhamento de pessoas.
        self.palette.set_index(new_index=len(persons_aligned.keys()))

        print("INDEX -- " + str(self.index_cor_bounding_box))
        print(self.colors_bounding_box[2])
        # Alinha os objetos
        object = AlignObjects(self.lst_legenda, self.lst_top_nomeadas_texto, self.lst_top_substantivos_objects,
                              self.list_boundingBoxOrganizada, self.directory, self.dict_lematizado,
                              self.index_cor_bounding_box, self.colors_bounding_box, self.group, self.palette)
        object_aligned, self.group = object.align(object_choose)

        self.titulo_noticia = self.titulo_noticia.replace("?", "")
        img_url = STATIC_REL + self.titulo_noticia + "_" + str(person_choose) + "_" + str(object_choose) + ".jpg"

        # reseta o indice
        self.palette.reset_colors()
        # Prepara o texto, legenda, titulo que serao destacados

        # try:
        [persons_aligned, object_aligned] = self._show_align_text(
            persons_aligned=persons_aligned, object_aligned=object_aligned
        )

        dic_avaliacao = {}
        # prepara o dicionario de avaliação
        if persons_aligned:
            for key, value in persons_aligned.items():
                dic_avaliacao[key] = ''

        if object_aligned:
            for key, value in object_aligned.items():
                dic_avaliacao[key] = ''
        # except Exception as e:
        #     print(e)

        self.palette.reset_colors()
        print("PROCESSO FINALIZADO")
        return persons_aligned, object_aligned, img_url, self.titulo_noticia, self.legenda, self.noticia, dic_avaliacao, self.group

    def align_manual(self, legenda, titulo, texto, img_path, person_choose, object_choose):
        """Alinha a partir de uma url fornecida pela usuario"""
        self.titulo_noticia = titulo
        self.legenda = legenda
        self.noticia = texto
        self.path_imagem = img_path

        self._set_manual_resources()
        self._process_text_image()

        # Alinha as pessoas
        person = AlignPersons(self.lst_legenda, self.lst_top_nomeadas_texto, self.list_boundingBoxOrganizada,
                              self.directory + "/img_original.jpg", self.directory + "/")
        persons_aligned = person.align(person_choose)

        # Alinha os objetos
        object = AlignObjects(self.lst_legenda, self.lst_top_nomeadas_texto, self.lst_top_substantivos_objects,
                              self.list_boundingBoxOrganizada)
        object_aligned = object.align(object_choose)

        print("PROCESSO FINALIZADO")

        img_url = STATIC_REL + self.titulo_noticia + "_" + str(person_choose) + "_" + str(object_choose) + ".jpg"
        return persons_aligned, object_aligned, img_url

    def _get_bounding_persons(self, boundingBox):
        bbox_pessoas = []
        for bounding in boundingBox:
            if bounding.objeto == "person":  # Se encontrar uma pessoa
                bbox_pessoas.append(bounding)
        return bbox_pessoas
