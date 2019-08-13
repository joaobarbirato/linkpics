from app.align_module import models
from app.src.UTIL import utils
from app.src.UTIL.crawlers import google_search_images as g_image
import cv2
from app.src.IA.face_recognition import FaceRecognition
import os

from config import STATIC_REL, BASE_DIR


class AlignPersons:
    def __init__(self, lst_legenda, lst_top_nomeadas_texto, list_boundingBoxOrganizada, path_img_original, path_noticia,
                 index_cor_bounding_box, colors_bounding_box, align_group, palette):
        self.pessoas_legenda = lst_legenda
        self.pessoas_texto = lst_top_nomeadas_texto
        self.list_boundingBoxOrganizada = list_boundingBoxOrganizada
        self.path_img_original = path_img_original
        self.path_noticia = path_noticia
        self.index_cor_bounding_box = index_cor_bounding_box
        self.colors_bounding_box = colors_bounding_box
        self.align_group = align_group
        self.palette = palette
        self.THR_GGL_IMG = 0.6
        self.THR_DLIB = 0.55

    def align(self, person_choosed):

        # Proposto
        if person_choosed == 1:
            return self._experiment_1()

        # Baseline
        elif person_choosed == 2:
            return self._experiment_2(), self.align_group

        else:
            return None

    def _get_bounding_persons(self):
        bbox_pessoas = []
        for bounding in self.list_boundingBoxOrganizada:
            if bounding.objeto == "person":  # Se encontrar uma pessoa
                bbox_pessoas.append(bounding)
        return bbox_pessoas

    def _experiment_1(self):
        """Alinhamento por entidade melhor classificada 
           e bounding box melhores classificadas
        """
        try:
            bbox_pessoas = self._get_bounding_persons()

            qtd_bbox_pessoas = len(bbox_pessoas)
            qtd_pessoas_legenda = len(self.pessoas_legenda)
            nomes_alinhamento = []

            if qtd_bbox_pessoas > 0:  # Se existirem pessoas para serem alinhadas
                if qtd_pessoas_legenda > 0:  # Se não houver nomes na legenda
                    nomes_alinhamento = list(
                        self.pessoas_legenda)  # copia para a lista oficial de nomes que serão alinhados

                for nome in self.pessoas_texto:  # para cada nome do texto
                    if nome.palavra not in nomes_alinhamento:
                        nomes_alinhamento.append(nome.palavra)  # adiciona o nome na lista
        except Exception as e:
            print(e)

        img_original = cv2.imread(STATIC_REL + "alinhamento2.jpg")

        dic_json = {}
        num_pessoa = 0

        while len(bbox_pessoas) > 0 and len(nomes_alinhamento) > 0:
            try:
                entidade = nomes_alinhamento[0]
                # texto += entidade.palavra + "= " + str(bbox_pessoas[0].imagem) + "\n"
                num_pessoa += 1

                palavra_radio_button = entidade.replace(" ", "_")
                dic_json[
                    entidade] = '<label><input type="radio" value="sim" name="radio_' + palavra_radio_button + '">Sim</label><span style="margin: 0 10px 0 10px;"></span>  <label><input type="radio"  value="nao" name="radio_' + palavra_radio_button + '">Não</label>'
                # dic_json[entidade.palavra] = "Pessoa "+str(num_pessoa)
                x, y, w, h = bbox_pessoas[0].Rect()

                # draw bounding box in img_original
                cv2.rectangle(img_original, (x, y), (x + w, y + h),
                              self.palette.next_color(type="bb", inc=True), 2)
                self.index_cor_bounding_box += 1

                alignment = models.Alignment(term=entidade, bounding_box=bbox_pessoas[0], is_ne=True)
                self.align_group.add_alignments(alignment=alignment)

                # remove a pessoa e a bounding box
                nomes_alinhamento.pop(0)
                bbox_pessoas.pop(0)
            except Exception as e:
                print(e)
        if img_original is not None:
            cv2.imwrite(STATIC_REL + "alinhamento2.jpg", img_original)
        return dic_json

    def _experiment_2(self):
        dic_json = {}
        bbox_pessoas = self._get_bounding_persons()

        img_original = None  # imagem original

        if len(self._get_bounding_persons()) > 0:  # Se existirem pessoas para serem alinhadas
            nomes_alinhamento = self._cluster_names()

            nomes_dlib = utils.file_to_List(BASE_DIR + "/data/alinhador/database_names.txt")

            dic_alinhamento = {}
            removed_Bbox = None  # variavel que armazena o bbox que sera removido caso encontre

            names_to_remove = []
            face_recognition = FaceRecognition()
            # Varre a lista de nomes

            for nome in nomes_alinhamento:
                nome_sem_acento = utils.removerAcentosECaracteresEspeciais(nome)
                if nome_sem_acento in nomes_dlib:  # se o nome existir nos dados do DLIB
                    img_original = cv2.imread(STATIC_REL + "alinhamento2.jpg")
                    for bBox in bbox_pessoas:  # para cada bounding box
                        new_sample = img_original.copy()
                        crop = new_sample[bBox.top:bBox.bot, bBox.left:bBox.right]
                        cv2.imwrite("bBoxImage.jpg", crop)
                        distancia = face_recognition.comparar_pessoas("bBoxImage.jpg", nome_sem_acento)
                        if isinstance(distancia, int) or isinstance(distancia, float):
                            print(nome, ": distancia < THR_DLIB: ", distancia < self.THR_DLIB)
                            if distancia < self.THR_DLIB and self._add_alignment(ne=nome, bbx=bBox):
                                # a face da Bbox corresponde com alguma imagem do nome no dlib
                                names_to_remove.append(nome)
                                dic_alinhamento[nome] = bBox  # grava o crop da imagem no dicionario
                                bBox.label = nome  # grava o nome na bBox
                                DIR_pessoa = BASE_DIR + "/data/alinhador/faceDB/lfw/" + nome_sem_acento.replace(" ", "_") + "/"
                                qtd_imagens = len([i for i in os.listdir(DIR_pessoa)]) + 1
                                # envia a crop da imagem para a pasta do dlib correspondente
                                os.rename("bBoxImage.jpg",
                                          DIR_pessoa + nome_sem_acento.replace(" ", "_") + "_" + str(qtd_imagens) + ".jpg")
                                removed_Bbox = bBox
                                names_to_remove.append(nome)
                                break  # vai para o proximo nome

                    if removed_Bbox in bbox_pessoas:
                        bbox_pessoas.remove(removed_Bbox)  # remove das Bbox uma face já alinhada
                else:
                    # busca as imagens da pessoa no google imagens
                    folder_g_image = g_image.get_images(nome_sem_acento)
                    print("CRIOU NOME: " + nome_sem_acento)
                    img_original = cv2.imread(STATIC_REL + "alinhamento2.jpg")
                    face_recognition.criar_db_g_images(folder_g_image)
                    for bBox in bbox_pessoas:  # para cada bounding box
                        new_sample = img_original.copy()
                        crop = new_sample[bBox.top:bBox.bot, bBox.left:bBox.right]  # corta a Bbox
                        cv2.imwrite("bBoxImage.jpg", crop)  # cria a imagem da Bbox
                        distancia = face_recognition.comparar_pessoas_google_imagens("bBoxImage.jpg", nome_sem_acento)
                        if isinstance(distancia, int) or isinstance(distancia, float):

                            if distancia < self.THR_GGL_IMG and self._add_alignment(ne=nome, bbx=bBox):
                                # a face da Bbox  corresponde com alguma imagem do google imagens
                                names_to_remove.append(nome)
                                dic_alinhamento[nome] = bBox  # grava o crop da imagem no dicionario
                                # bBox.label = nome  # grava o nome na bBox
                                DIR_pessoa = BASE_DIR + "/data/alinhador/faceDB/lfw/" + nome_sem_acento.replace(" ", "_") + "/"
                                if not os.path.exists(DIR_pessoa):
                                    os.makedirs(DIR_pessoa)
                                qtd_imagens = len([i for i in os.listdir(DIR_pessoa)]) + 1
                                # envia a crop da imagem para a pasta do dlib correspondente
                                os.rename("bBoxImage.jpg",
                                          DIR_pessoa + nome_sem_acento.replace(" ", "_") + "_" + str(qtd_imagens) + ".jpg")
                                nomes_dlib.append(nome)
                                utils.escrever_arquivo_from_list(nomes_dlib, BASE_DIR + "/data/alinhador/database_names.txt")
                                removed_Bbox = bBox
                                names_to_remove.append(nome)
                                break  # Quando encontra sai e vai para o próximo nome
                    if removed_Bbox in bbox_pessoas:
                        bbox_pessoas.remove(removed_Bbox)  # remove das Bbox uma face já alinhada

            texto = ""
            num_pessoa = 0

            for entidade, value in dic_alinhamento.items():
                texto += entidade + "= " + str(value.imagem) + "\n"
                num_pessoa += 1
                palavra_radio_button = entidade.replace(" ", "_")
                dic_json[
                    entidade] = '<label><input type="radio" value="sim" name="radio_' + palavra_radio_button + '">Sim</label><span style="margin: 0 10px 0 10px;"></span>  <label><input type="radio"  value="nao" name="radio_' + palavra_radio_button + '">Não</label>'
                x, y, w, h = value.Rect()

                print("ENTIDADE:" + entidade)
                cv2.rectangle(img_original, (x, y), (x + w, y + h),
                              self.palette.next_color(type="bb", inc=True), 2)
                self.index_cor_bounding_box += 1

            if img_original is not None:
                cv2.imwrite(STATIC_REL + "alinhamento2.jpg", img_original)

            path_arquivo = self.path_noticia + "alinhamento_pessoas.txt"
            utils.escrever_arquivo(texto, path_arquivo)
            return dic_json

    def _add_alignment(self, ne="", bbx=None):
        if ne and bbx is not None:
            if not self.align_group.has_alignment(term=ne):
                bbx.label = ne
                alignment = models.Alignment(term=ne, bounding_box=bbx, is_ne=True)
                self.align_group.add_alignments(alignment=alignment)
                return True

        return False

    def _cluster_names(self):
        nomes_alinhamento = list(set(self.pessoas_legenda).union(set([en.palavra for en in self.pessoas_texto])))
        for na_1 in nomes_alinhamento:
            for na_2 in nomes_alinhamento:
                if na_2 != na_1:
                    if na_2 != na_1 and na_2 in na_1 or na_2 == utils.removerAcentosECaracteresEspeciais(na_1):
                        nomes_alinhamento.remove(na_2)
                        break

        print('[EXP_2|_CLUSTER_NAMES nomes_alinhamento]:', nomes_alinhamento)
        return nomes_alinhamento
