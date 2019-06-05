import cv2
import operator
import os
import re
from collections import deque
from nltk.corpus import wordnet as wn

from app.align_module.models import Alignment
from app.src.PLN.WordNetClasses import TrazerSynsetBoundingBox
from app.src.PLN.trocar_nomes import TrocarNomes
from app.src.UTIL import utils
from config import STATIC_REL


def get_next_occurrence_dict(dict, word):
    """
    Get the latest index of a word in a dictionary, where indexes are concatenated after a '#'
    :param dict: dictionary
    :param word: key for getting latest index
    :return: next index
    """
    pattern = r"([a-zA-Z]*)#(\d*)"
    query = 0
    for key, _ in dict.items():
        if word in key:
            parsed = re.search(pattern=pattern, string=key)
            if parsed is not None:
                (_, occurrence) = [t(s) for t, s in zip((str, int), parsed.groups())]
                if occurrence > query:
                    query = occurrence

    return str(query + 1)


def add_dic_alinhamento(dict, word, nun_obj):
    """
    Function for 1:n alignment
    :param dict: dic_alinhamento
    :param word: key word for dictionary
    :param nun_obj: value for key
    :return: updated dictionary
    """
    if word in dict:
        dict[word + "#" + get_next_occurrence_dict(dict=dict, word=word)] = dict[word]
    else:
        dict[word] = nun_obj
    return dict


class AlignObjects:
    def __init__(self, lst_legenda, lst_top_nomeadas_texto, lst_substantivos,
                 list_boundingBoxOrganizada, path_folder, dict_lematizado, index_cor_bounding_box, colors_bounding_box,
                 align_group, palette):
        self.lst_legenda = lst_legenda
        self.lst_top_nomeadas_texto = lst_top_nomeadas_texto
        self.lst_substantivos = lst_substantivos
        self.list_boundingBoxOrganizada = list_boundingBoxOrganizada
        self.path_folder = path_folder
        self.dict_lematizado = dict_lematizado
        self.index_cor_bounding_box = index_cor_bounding_box
        self.colors_bounding_box = colors_bounding_box
        self.align_group = align_group
        self.palette = palette
        self.thr = 0.82

    def align(self, object_choosed):

        # Proposto
        if object_choosed == 1:
            return self._experiment_1(), self.align_group

        # Baseline
        elif object_choosed == 5:
            return self._experiment_5()

        else:
            return None

    def read_words_visual(self, arquivo_txt):
        open_file = open(arquivo_txt, 'r')
        words_list = []
        contents = open_file.readlines()
        for content in contents:
            content = content.replace('\n', '')
            if content not in words_list:
                words_list.append(content)
        open_file.close()
        return words_list

    def _get_bounding_objects(self):
        bbox_objects = []
        for bounding in self.list_boundingBoxOrganizada:
            if bounding.objeto != "person":  # Se encontrar uma pessoa
                bbox_objects.append(bounding)
        return bbox_objects

    def _ordenar_bbox_tamanho(self, bbox_objects):

        ordered_bbox = []
        numero_repeticoes = len(bbox_objects)  # pega o total de bounding box
        count = 0
        while count < numero_repeticoes:
            maior_area = 0
            indice_maior_area = -1
            total_bounding = len(bbox_objects)  # total de bounding box restantes

            for i in range(0, total_bounding):
                area = bbox_objects[i].width * bbox_objects[i].height
                if area > maior_area:
                    maior_area = area  # guarda a menor distancia
                    indice_maior_area = i  # guarda o indice da menor distancia

            ordered_bbox.append(bbox_objects[
                                    indice_maior_area])  # coloca na lista o Bounding box de menor distancia
            ordered_bbox[count].area = maior_area
            ordered_bbox[count].imagem = count
            bbox_objects.remove(bbox_objects[indice_maior_area])
            count = count + 1
        return ordered_bbox

    def _experiment_5(self):
        """ Tamanho do objeto com a palavra melhor classificada """
        print('experimento 5')
        bbox_objects = self._get_bounding_objects()
        bbox_objects = self._ordenar_bbox_tamanho(bbox_objects)

        img_original = cv2.imread(STATIC_REL + "alinhamento2.jpg")
        dic_json = {}

        # return dic_json
        while len(bbox_objects) > 0 and len(self.lst_substantivos) > 0:
            try:
                palavra = self.lst_substantivos[0]
                # texto += entidade.palavra + "= " + str(bbox_pessoas[0].imagem) + "\n"
                # num_objeto += 1
                palavra_radio_button = palavra.replace(" ", "_")
                dic_json[
                    palavra] = '<label><input type="radio" value="sim" name="radio_' + palavra_radio_button + '">Sim</label><span style="margin: 0 10px 0 10px;"></span>  <label><input type="radio"  value="nao" name="radio_' + palavra_radio_button + '">Não</label>'

                # dic_json[palavra] = "Objeto " + str(num_objeto)
                x, y, w, h = bbox_objects[0].Rect()

                # draw bounding box in img_original
                cv2.rectangle(img_original, (x, y), (x + w, y + h),
                              self.palette.next_color(type="bb", inc=True), 2)
                self.index_cor_bounding_box += 1
                # remove a pessoa e a bounding box
                self.lst_substantivos.pop(0)
                bbox_objects.pop(0)
            except Exception as e:
                print(e)
                
        if img_original is not None:
            cv2.imwrite(STATIC_REL + "alinhamento2.jpg", img_original)
        return dic_json

    def _experiment_1(self):
        """Experimento 4 + Experimento 2"""
        global maior_distancia
        print('experimento 1')
        arquivo_wup = "/wup_top5.txt"
        img_original = cv2.imread(STATIC_REL + "alinhamento2.jpg")
        bbox_objects = self._get_bounding_objects()
        num_objeto = 0
        lst_palavras_visuais = self.read_words_visual("visual_words.txt")

        for bbox in bbox_objects:
            bbox.lst_cnn.append(bbox.objeto)

        dic_json = {}

        #               S I M I L A R I D A D E       W U P
        dic_alinhamento = {}

        if not bbox_objects:
            return dic_json

        for bbox in bbox_objects:
            # cria uma pasta com nome {num_foto-nome_objeto}
            object_name = str(bbox.imagem) + "-" + bbox.objeto
            if not os.path.exists(self.path_folder + "/" + object_name):
                os.mkdir(self.path_folder + "/" + object_name)
            dir_objeto = self.path_folder + "/" + object_name

            # dicionario para calcular as distancias da palavra da Bbox para todos substantivos
            dicionario_distancias_wup = {}

            for substantivo in self.lst_substantivos:
                maior_distancia = 0
                lst_synsets = wn.synsets(substantivo, pos=wn.NOUN)
                for j in range(0, len(lst_synsets)):
                    # pega um dos synsets referentes ao substantivo
                    synset = str(lst_synsets[j])
                    synset = synset.replace("Synset('", "")
                    synset = synset.replace("')", "")
                    word_substantivo = wn.synset(synset)
                    for palavra in bbox.lst_cnn:
                        palavra_bbox = palavra  # obtém a palavra que está na Bbox
                        palavra_bbox = TrocarNomes(palavra_bbox)
                        word_bounding = TrazerSynsetBoundingBox(palavra_bbox)  # synset da bbox

                        if word_bounding is None:
                            lst_synsets_cnn = wn.synsets(palavra_bbox, pos=wn.NOUN)
                            for k in range(0, len(lst_synsets_cnn)):
                                synset = str(lst_synsets_cnn[
                                                 k])  # pega um dos synsets referentes ao substantivo
                                synset = synset.replace("Synset('", "")
                                synset = synset.replace("')", "")
                                word_bounding = wn.synset(synset)

                                try:
                                    distancia_wup = word_substantivo.wup_similarity(word_bounding)
                                except:
                                    distancia_wup = 0
                                if distancia_wup > maior_distancia:
                                    maior_distancia = distancia_wup
                                    # index_maior_palavra = i
                                    # palavra_ranqueada = substantivo
                        else:
                            try:
                                pass

                            except:
                                distancia_wup = 0
                                if distancia_wup > maior_distancia:
                                    maior_distancia = distancia_wup

                print("maior distancia: ", maior_distancia)
                if maior_distancia > self.thr:
                    dicionario_distancias_wup[substantivo] = maior_distancia
                print(dicionario_distancias_wup)

            if dicionario_distancias_wup:
                sorted_wup = sorted(
                    dicionario_distancias_wup.items(), key=operator.itemgetter(1), reverse=True)

                wup_deque = deque()

                palavra_ranqueada = sorted_wup[0][0]

                # para cada palavra da sorted wup (0 a 4)
                if sorted_wup[0][0] not in lst_palavras_visuais:
                    for z in range(0, 5):
                        try:
                            # verifica se esta na lista das palavras visuais
                            if sorted_wup[z][0].lower() in lst_palavras_visuais:
                                wup_deque.appendleft(sorted_wup[z][0])
                            else:
                                wup_deque.append(sorted_wup[z][0])
                        except:
                            pass

                        # se estiver sobe uma posicao na lista
                    palavra_ranqueada = wup_deque[0]

                dic_alinhamento = add_dic_alinhamento(dict=dic_alinhamento, word=palavra_ranqueada, nun_obj=num_objeto)

                num_objeto += 1
                # ESCREVE NO DIRETORIO O TOP-5
                top5 = ""
                for z in range(0, 5):
                    try:
                        top5 += self.dict_lematizado[sorted_wup[z][0].lower()] + "-------" + str(sorted_wup[z][1]) + "\n"
                    except:
                        pass
                utils.escrever_arquivo(top5, dir_objeto + arquivo_wup)

                alignment = Alignment(term=palavra_ranqueada, bounding_box=bbox)
                self.align_group.add_alignments(alignment=alignment)
        # _________________ALINHAMENTO________________
        for palavra, value in dic_alinhamento.items():
            # dic_json[palavra] = "Objeto " + str(dic_alinhamento[palavra])
            palavra_radio_button = palavra.replace(" ", "_")
            dic_json[
                palavra] = '<label><input type="radio" value="sim" name="radio_' + palavra_radio_button + \
                           '">Sim</label><span style="margin: 0 10px 0 10px;"></span>  <label><input type="radio" ' + \
                           '  value="nao" name="radio_' + palavra_radio_button + '">Não</label>'
            x, y, w, h = bbox_objects[0].Rect()

            # draw bounding box in img_original

            cv2.rectangle(img_original, (x, y), (x + w, y + h), self.palette.next_color(type="bb", inc=True),
                          2)
            self.index_cor_bounding_box += 1

            # remove a bounding box
            bbox_objects.pop(0)

        if img_original is not None:
            cv2.imwrite(STATIC_REL + "alinhamento2.jpg", img_original)

        return dic_json
