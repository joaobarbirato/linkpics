import os
from nltk.corpus import wordnet as wn
from treetagger import TreeTagger

from app.src.PLN.chunk_sintagmas import MWEChunker
from app.src.PLN.coreference import CoreferenceDocument
from app.src.util.corenlp import CoreNLPWrapper
from .entidade_nomeada import EntidadeNomeada
from .reconhecimento_nomeada import *
from .word import Palavra

lst_todasNoticias = []
lst_treetagger = []
lst_palavras_originais = []
lst_substantivosValidos = []

lst_ner = []


def get_word_from_lemma(lemma=None):
    global lst_treetagger
    for [_word, _, _lemma] in lst_treetagger:
        if _lemma == lemma or _lemma == lemma.upper() or _lemma == lemma.title():
            return _word


class AplicadorPLN(object):
    crefdoc: CoreferenceDocument

    # -----------------------------------V A R I Á V E I S --- G L O B A I S---------------------

    def __init__(self, path_projeto, noticia, legenda, titulo, path, path_dir):
        self.path_projeto = path_projeto
        self.diretorio = path_projeto + path_dir
        self.path_noticia = path_projeto + path
        self.noticia = noticia
        self.noticia_inicial = noticia
        self.legenda = legenda
        self.titulo = titulo
        self.lst_top_substantivos = []
        self.lst_top_entidades_nomeadas = []
        self.total_entidades = 0
        self.tipo_wordNet = ""
        self.lst_EntidadesNomeadas = []
        self.lst_interseccao_entidades = []
        self.lst_top_substantivos_physical = []
        self.lst_top_substantivos_objects = []
        self.lst_diferenca_entidades = []
        self.dict_lematizado = {}
        self.chunker = MWEChunker()

        self.crefdoc = CoreferenceDocument()
        self.snt_tok = []

        PATH_LOCATION = os.path.dirname(os.path.abspath(__file__))
        print(PATH_LOCATION)

        TREE_TAGGER_PATH = PATH_LOCATION + '/TreeTagger'
        print('exportando tree tagger em ', TREE_TAGGER_PATH)
        os.environ["TREETAGGER_HOME"] = TREE_TAGGER_PATH

        self.tree_tagger = TreeTagger(language='english')

    def SomentePalavras_physical(self):
        lst_palavras = []
        for x in range(0, len(self.lst_top_substantivos_physical)):
            lst_palavras.append(self.lst_top_substantivos_physical[x].palavra)
        return lst_palavras

    def file_to_List(self, file_name):
        lista = []
        with open(file_name, 'rt') as f:
            for line in f:
                lista.append(line.replace('\n', ''))
        return lista

    def SomentePalavras_objects(self):
        lst_palavras = []
        for x in range(0, len(self.lst_top_substantivos_objects)):
            lst_palavras.append(self.lst_top_substantivos_objects[x].palavra)
        return lst_palavras

    def read_words(self, arquivo_txt):
        open_file = open(arquivo_txt, 'r')
        words_list = []
        contents = open_file.readlines()
        for i in range(len(contents)):
            words_list.extend(contents[i].split())
        open_file.close()
        return words_list

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

    # Filtra o texto removendo caracteres que atrapalham o TreeTagger e EN.
    def FiltrarTexto(self):
        self.noticia = self.noticia.replace("'s", " ")
        self.noticia = self.noticia.replace("'s", " ")
        self.noticia = self.noticia.replace("//", " ")
        self.noticia = self.noticia.replace("%,", " ")
        self.noticia = self.noticia.replace("%:", " ")
        self.noticia = self.noticia.replace("%?", " ")
        self.noticia = self.noticia.replace("%!", " ")
        self.noticia = self.noticia.replace("%.", " ")
        self.noticia = self.noticia.replace("%", " ")
        self.noticia = self.noticia.replace(":", ". ")
        self.noticia = self.noticia.replace(".", ". ")
        self.noticia = self.noticia.replace(";", " ")
        self.noticia = self.noticia.replace("n't", " not")
        self.noticia = self.noticia.replace("?T", "? T")
        self.noticia = self.noticia.replace("I'm", "I am")
        self.noticia = self.noticia.replace('"', '')
        self.noticia = self.noticia.replace("[", "")
        self.noticia = self.noticia.replace("]", "")
        self.noticia = self.noticia.replace("?", "")
        self.noticia = self.noticia.replace("'", "")
        self.noticia = self.noticia.replace("(", "")
        self.noticia = self.noticia.replace(")", "")
        self.noticia = self.noticia.replace('–', ' ')
        self.noticia = self.noticia.replace("´", "")
        self.noticia = self.noticia.replace("-", " ")
        self.noticia = self.noticia.replace(" , ", " ")
        self.noticia = self.noticia.replace("Translated by TOM GATEHOUSE", " ")

    # -----------------TREE TAGGER e STANFORD NER

    def AplicarStanforNER_legenda(self):
        lst_ner_temp = self.stanfordner.tag(self.legenda.split())
        # Junta entidades nomeadas  da mesma pessoa
        lst_ner = []
        for x in range(0, len(lst_ner_temp)):
            if x < (len(lst_ner_temp) - 1):
                if lst_ner_temp[x][1] == "PERSON":
                    entidade = lst_ner_temp[x][0]
                    if lst_ner_temp[x + 1][1] == "PERSON":
                        entidade += " " + lst_ner_temp[x + 1][0]
                    lst_ner.append(entidade)
        return lst_ner

    def AplicarTreeTagger(self):
        global lst_treetagger
        lst_treetagger = []
        lst_treetagger_temp = self.tree_tagger.tag(self.noticia)
        num_palavras_tagger = len(lst_treetagger_temp)
        # Remove as pontuações do tree tagger gerando uma nova lista
        for x in range(0, num_palavras_tagger):
            if lst_treetagger_temp[x][0] != "." and lst_treetagger_temp[x][0] != "!" and lst_treetagger_temp[x][
                0] != "?" and lst_treetagger_temp[x][0] != ":" and lst_treetagger_temp[x][0] != ";" and \
                    lst_treetagger_temp[x][0] != "," and lst_treetagger_temp[x][0] != "(" and lst_treetagger_temp[x][
                0] != ")" and lst_treetagger_temp[x][0] != '"' and lst_treetagger_temp[x][0] != "'" and \
                    lst_treetagger_temp[x][0] != "´" and lst_treetagger_temp[x][0] != "`":
                lst_treetagger.append(lst_treetagger_temp[x])

    def AplicarChunk(self):
        global lst_treetagger
        if self.chunker.set_list_tt(lst_treetagger):
            lst_treetagger = self.chunker.chunk()

    def ResolveCoreferences(self):
        """

        :return:
        """

        _snt_titulo = self.titulo
        if '.' not in self.titulo:
            _snt_titulo += '.'

        _snt_legenda = self.legenda
        if '.' not in self.legenda and self.legenda != '':
            _snt_legenda += '.'

        sentences = f'{_snt_titulo} {_snt_legenda} {self.noticia}'

        sentences = sentences.replace('"', '')
        # TODO: Resolution with quotes in text

        cnlpw = CoreNLPWrapper()
        coref_dict = cnlpw.coreference_resolution(sentences=sentences, comm=True)
        self.crefdoc.load_dict(coref_dict, sentences)
        _tokenizeds = self.crefdoc.get_tkn_snts()

        self.snt_tok = [element for element in
                        zip([' '.join([str(token) for token in token_list]) for token_list in _tokenizeds],
                            _tokenizeds)]

    def get_crefdoc(self):
        return self.crefdoc

    def get_snt_tok(self):
        return self.snt_tok

    def AplicarStanforNER(self):
        lst_ner = self.stanfordner.tag(self.noticia.split())
        return lst_ner

    # ---- Filtra a palavra e devolve se for substantivo

    def FiltrarSubstantivos(self, treetagger_pos):
        tipo_morfo = treetagger_pos[1]
        if "NP" in tipo_morfo or "NPS" in tipo_morfo or "NN" in tipo_morfo or "NNS" in tipo_morfo:
            return 1
        else:
            return -1

    # -----------------------FUNÇÃO MAIS IMPORTANTE DO SISTEMA-------------------

    def ObterEntidadesNomeadas_SubstantivosValidos(self, tipo):  #
        self.tipo_wordNet = tipo
        global lst_substantivosValidos
        lst_substantivosValidos = []
        self.lst_EntidadesNomeadas = []
        # percorre o texto  original e do treetagger e atribui indices para o tree tagger
        global lst_ner
        lst_ner = []
        # lst_ner = self.AplicarStanforNER()
        lst_entidades_nltk = TrazerEntidadesNomeadas(self.path_noticia)
        entidades = []
        nomes_texto = []

        # Filtra as entidades nomeadas removendo duplicidade
        for entidade in lst_entidades_nltk:
            remover = False
            a = entidade.split(" ")
            for x in a:
                if x not in nomes_texto:
                    nomes_texto.append(x)
                else:
                    remover = True
            if not remover:
                entidades.append(entidade)

        for entidade_nomeada in entidades:

            max_ocorrencias = 0
            presente_titulo = 0
            presente_legenda = 0

            for nome in entidade_nomeada.split():
                ocorrencias = self.ContarNumeroEntidadesNomeadas(nome)
                if ocorrencias > max_ocorrencias:
                    max_ocorrencias = ocorrencias

                legenda = self.VerificarPresencaLegenda(nome)
                if legenda != 0:
                    presente_legenda = 1

                titulo = self.VerificarPresencaTitulo(nome)
                if titulo != 0:
                    presente_titulo = 1

            entidade = EntidadeNomeada(
                entidade_nomeada, max_ocorrencias, presente_legenda, presente_titulo)
            self.lst_EntidadesNomeadas.append(entidade)

        print("TITULO DA NOTICIA:" + self.titulo)
        texto_lematizado = ''
        palavras_fisicas = []
        if [''] in lst_treetagger:
            lst_treetagger.remove([''])
        for x in range(0, len(lst_treetagger)):
            # Monta o dict de palavras lematizadas
            self.dict_lematizado[lst_treetagger[x][2].lower()] = lst_treetagger[x][0]

            word_filtrada = lst_treetagger[x][2]
            tipo_morfo = lst_treetagger[x][1]
            lema = lst_treetagger[x][2]
            texto_lematizado += ' ' + lema
            entidade_nomeada = "O"

            if word_filtrada in lst_entidades_nltk:
                entidade_nomeada = "PERSON"

            p = Palavra(x, word_filtrada, tipo_morfo, lema,
                        entidade_nomeada, "", "", 0, 0, 1, 0, 0, x)

            if entidade_nomeada == "O":
                retorno = self.FiltrarSubstantivos(lst_treetagger[x])
                if retorno == 1:
                    palavra_fisica = self.DescobrirPalavraFisica(
                        word_filtrada, tipo)  # descobre se a palavra é fisica a partir do tipo desejado(
                    # physical_entity,object)
                # se for substantivo,palavra fisica(segundo wordNet), e NÃO for nem localizacao e nem organizacao
                # ->coloca no list
                if retorno == 1 and palavra_fisica == 1 and entidade_nomeada != "ORGANIZATION" and entidade_nomeada != "LOCATION":
                    palavras_fisicas.append(word_filtrada)
                    # verifica se a palavra está na legenda
                    legenda = self.VerificarPresencaLegenda(word_filtrada)
                    p.presente_legenda = legenda
                    # verifica se a palavra está no título
                    titulo = self.VerificarPresencaTitulo(word_filtrada)
                    p.presente_titulo = titulo
                    lst_substantivosValidos.append(p)  # grava no list

        # self.PreencherAnteriorPosterior()  # preenche as palavras anteriores e posteriores

        # ---------------Substantivos--------------

        # self.ContarDocumentos_substantivos()
        # self.ContarNumeroPalavrasCorpus_substantivos()
        print('TEXTO LEMATIZADO:' + texto_lematizado)
        print(palavras_fisicas)
        self.ContarNumeroPalavrasTexto_substantivos()

    # ---------------Entidades Nomeadas--------------
    # self.ContarDocumentos_entidadesNomeadas()
    # self.ContarNumeroPalavrasCorpus_entidadesNomeadas()
    # self.ContarNumeroPalavrasTexto_entidades_nomeadas()

    # -----------------OrganizarTopSubstantivos---------------Funções

    def get_dict_lematizado(self):
        return self.dict_lematizado

    def VerificarPresencaLegenda(self, palavra):

        lst_palavrasLegenda = self.ObterPalavrasLegenda()
        for x in range(0, len(lst_palavrasLegenda)):
            if lst_palavrasLegenda[x] == palavra:
                return 1
        return 0

    def VerificarPresencaTitulo(self, palavra):
        lst_palavrasTitulo = self.ObterPalavrasTitulo()
        for x in range(0, len(lst_palavrasTitulo)):
            if lst_palavrasTitulo[x] == palavra:
                return 1
        return 0

    def ObterPalavrasLegenda(self):
        return self.legenda.split()

    def ObterPalavrasTitulo(self):
        return self.titulo.split()

    def PreencherAnteriorPosterior(self):
        total_palavras = len(self.lst_EntidadesNomeadas)
        global lst_ner

        for x in range(0, total_palavras):

            if x != 0:
                index = self.lst_EntidadesNomeadas[x].indice_treetagger - 1
                try:
                    entidade_nomeada = lst_ner[index][1]
                except:
                    entidade_nomeada = "O"
                if entidade_nomeada == "PERSON":
                    juncao_string1 = self.lst_EntidadesNomeadas[x - 1].palavra + \
                                     "." + self.lst_EntidadesNomeadas[x].palavra
                    juncao_string2 = self.lst_EntidadesNomeadas[x - 1].palavra + \
                                     ". " + self.lst_EntidadesNomeadas[x].palavra
                    if juncao_string1 not in self.noticia and juncao_string2 not in self.noticia:
                        self.lst_EntidadesNomeadas[x].anterior = self.lst_EntidadesNomeadas[x - 1].palavra

                    # se não for a ultima palavra do texto, pega a palavra posterior
            if x != total_palavras - 1:
                indexPos = self.lst_EntidadesNomeadas[x].indice_treetagger + 1
                try:
                    entidade_nomeada = lst_ner[indexPos][1]
                except:
                    entidade_nomeada = "O"

                if entidade_nomeada == "PERSON":
                    juncao_string1 = self.lst_EntidadesNomeadas[x].palavra + \
                                     "." + self.lst_EntidadesNomeadas[x + 1].palavra
                    juncao_string2 = self.lst_EntidadesNomeadas[x].palavra + \
                                     ". " + self.lst_EntidadesNomeadas[x + 1].palavra
                    if juncao_string1 not in self.noticia and juncao_string2 not in self.noticia:
                        self.lst_EntidadesNomeadas[x].posterior = self.lst_EntidadesNomeadas[x + 1].palavra

    def ContarNumeroPalavrasTexto_entidades_nomeadas(self):
        total_palavras = len(self.lst_EntidadesNomeadas)
        for x in range(0, total_palavras):
            palavra = self.lst_EntidadesNomeadas[x].palavra
            for y in range(0, total_palavras):
                if self.lst_EntidadesNomeadas[
                    y].palavra == palavra:  # se a palavra for igual a palavra do documento, adiciona +1 no numero de documentos que aparece a palavra
                    self.lst_EntidadesNomeadas[x].ocorrencias = self.lst_EntidadesNomeadas[x].ocorrencias + 1

    def ContarNumeroPalavrasTexto_substantivos(self):
        total_palavras = len(lst_substantivosValidos)
        for x in range(0, total_palavras):
            palavra = lst_substantivosValidos[x].palavra
            for y in range(0, total_palavras):
                if lst_substantivosValidos[
                    y].palavra == palavra:  # se a palavra for igual a palavra do documento, adiciona +1 no numero de documentos que aparece a palavra
                    lst_substantivosValidos[x].ocorrencias = lst_substantivosValidos[x].ocorrencias + 1

    def ContarNumeroPalavrasCorpus_entidadesNomeadas(self):
        total_palavras = len(self.lst_EntidadesNomeadas)
        for x in range(0, total_palavras):
            palavra = self.lst_EntidadesNomeadas[x].palavra
            for documento in lst_todasNoticias:  # para cada documento faça
                for word in documento:  # para cada palavra no documento
                    if word == palavra:  # se a palavra for igual a palavra do documento, adiciona +1 no numero de documentos que aparece a palavra
                        self.lst_EntidadesNomeadas[
                            x].total_palavras_documentos = self.lst_EntidadesNomeadas[x].total_palavras_documentos + 1

    def ContarNumeroPalavrasCorpus_substantivos(self):
        total_palavras = len(lst_substantivosValidos)
        for x in range(0, total_palavras):
            palavra = lst_substantivosValidos[x].palavra
            for documento in lst_todasNoticias:  # para cada documento faça
                for word in documento:  # para cada palavra no documento
                    if word == palavra:  # se a palavra for igual a palavra do documento, adiciona +1 no numero de documentos que aparece a palavra
                        lst_substantivosValidos[
                            x].total_palavras_documentos = lst_substantivosValidos[x].total_palavras_documentos + 1

    def ContarDocumentos_entidadesNomeadas(self):
        total_palavras = len(self.lst_EntidadesNomeadas)
        for x in range(0, total_palavras):
            palavra = self.lst_EntidadesNomeadas[x].palavra
            for documento in lst_todasNoticias:  # para cada documento faça
                for word in documento:  # para cada palavra no documento
                    if word == palavra:  # se a palavra for igual a palavra do documento, adiciona +1 no numero de documentos que aparece a palavra
                        self.lst_EntidadesNomeadas[x].numero_documentos = self.lst_EntidadesNomeadas[
                                                                              x].numero_documentos + 1
                        break  # para o for caso encontre a palavra.

    def ContarDocumentos_substantivos(self):
        total_palavras = len(lst_substantivosValidos)
        for x in range(0, total_palavras):
            palavra = lst_substantivosValidos[x].palavra
            for documento in lst_todasNoticias:  # para cada documento faça
                for word in documento:  # para cada palavra no documento
                    if word == palavra:  # se a palavra for igual a palavra do documento, adiciona +1 no numero de documentos que aparece a palavra
                        lst_substantivosValidos[x].numero_documentos = lst_substantivosValidos[x].numero_documentos + 1
                        break  # para o for caso encontre a palavra.

    def ContarNumeroEntidadesNomeadas(self, entidade):
        ocorrencias = 0
        for palavra in lst_treetagger:
            if entidade == palavra[0]:
                ocorrencias += 1
        return ocorrencias

    # ----------------Remover palavras duplicadas e para acoplar entidades nomeadas umas com as outras

    def RemoverPalavras_EntidadesNomeadas(self):
        total_palavras = len(self.lst_EntidadesNomeadas)
        lst_palavras_excluidas = []
        for x in range(0, total_palavras):

            entidade_nomeada = self.lst_EntidadesNomeadas[x].entidade_nomeada
            posterior = self.lst_EntidadesNomeadas[x].posterior
            if entidade_nomeada == "PERSON":
                if posterior != "":  # se posterior não for vazio
                    # procura a ocorrencia da palavra posterior no list e acopla as informações
                    for i in range(0, total_palavras):
                        palavra = self.lst_EntidadesNomeadas[i].palavra

                        if palavra == posterior:  # se encontrar a palavra, acopla as informações

                            self.lst_EntidadesNomeadas[
                                x].palavra_completa = self.lst_EntidadesNomeadas[
                                                          x].palavra_completa + " " + palavra  # concatena a palavra
                            self.lst_EntidadesNomeadas[x].segundo_nome = palavra
                            # adiciona essa palavra para excluir
                            lst_palavras_excluidas.append(palavra)
                            # se as ocorrencias forem maiores
                            if self.lst_EntidadesNomeadas[i].ocorrencias > self.lst_EntidadesNomeadas[x].ocorrencias:
                                self.lst_EntidadesNomeadas[x].ocorrencias = self.lst_EntidadesNomeadas[i].ocorrencias

                            # se o numero de documentos forem maiores
                            if self.lst_EntidadesNomeadas[i].numero_documentos > self.lst_EntidadesNomeadas[
                                x].numero_documentos:
                                self.lst_EntidadesNomeadas[x].numero_documentos = self.lst_EntidadesNomeadas[
                                    i].numero_documentos

                            # se o total de palavras documentos forem maiores
                            if self.lst_EntidadesNomeadas[i].total_palavras_documentos > self.lst_EntidadesNomeadas[
                                x].total_palavras_documentos:
                                self.lst_EntidadesNomeadas[x].total_palavras_documentos = self.lst_EntidadesNomeadas[
                                    i].total_palavras_documentos

                            # se estiver na legenda
                            if self.lst_EntidadesNomeadas[i].presente_legenda == 1:
                                self.lst_EntidadesNomeadas[x].presente_legenda = 1
                            # se estiver no titulo
                            if self.lst_EntidadesNomeadas[i].presente_titulo == 1:
                                self.lst_EntidadesNomeadas[x].presente_titulo = 1
                            # pega um terceiro nome
                            posterior_pos = self.lst_EntidadesNomeadas[i].posterior
                            if posterior_pos != "":  # se posterior não for vazio
                                # procura a ocorrencia da palavra posterior no list e acopla as informações
                                for j in range(0, total_palavras):
                                    palavra = self.lst_EntidadesNomeadas[j].palavra

                                    if palavra == posterior_pos:  # se encontrar a palavra, acopla as informações

                                        self.lst_EntidadesNomeadas[
                                            x].palavra_completa = self.lst_EntidadesNomeadas[
                                                                      x].palavra_completa + " " + palavra  # concatena a palavra
                                        self.lst_EntidadesNomeadas[x].terceiro_nome = palavra
                                        # adiciona essa palavra para excluir
                                        lst_palavras_excluidas.append(palavra)
                                        # se as ocorrencias forem maiores
                                        if self.lst_EntidadesNomeadas[j].ocorrencias > self.lst_EntidadesNomeadas[
                                            x].ocorrencias:
                                            self.lst_EntidadesNomeadas[x].ocorrencias = self.lst_EntidadesNomeadas[
                                                j].ocorrencias

                                        # se o numero de documentos forem maiores
                                        if self.lst_EntidadesNomeadas[j].numero_documentos > self.lst_EntidadesNomeadas[
                                            x].numero_documentos:
                                            self.lst_EntidadesNomeadas[x].numero_documentos = \
                                                self.lst_EntidadesNomeadas[
                                                    j].numero_documentos

                                        # se o total de palavras documentos forem maiores
                                        if self.lst_EntidadesNomeadas[j].total_palavras_documentos > \
                                                self.lst_EntidadesNomeadas[x].total_palavras_documentos:
                                            self.lst_EntidadesNomeadas[x].total_palavras_documentos = \
                                                self.lst_EntidadesNomeadas[
                                                    j].total_palavras_documentos

                                        # se estiver na legenda
                                        if self.lst_EntidadesNomeadas[j].presente_legenda == 1:
                                            self.lst_EntidadesNomeadas[j].presente_legenda = 1
                                        # se estiver no titulo
                                        if self.lst_EntidadesNomeadas[j].presente_titulo == 1:
                                            self.lst_EntidadesNomeadas[x].presente_titulo = 1
        # agora exclui do list as palavras que são segundo e terceiros nomes
        # para cada palavra, excluir todas ocorrencias
        for w in range(0, len(lst_palavras_excluidas)):
            existe_palavra = 1
            while existe_palavra == 1:  # se for == 0 sai do loop e vai para a proxima palavra
                total_palavras = len(self.lst_EntidadesNomeadas)
                palavra = lst_palavras_excluidas[w]
                for j in range(0, total_palavras):  # varre o list e exclui a palavra do list
                    existe_palavra = 0  # nao existe a palavra, a menos que a encontre
                    # se encontrar a palavra, exclui do list
                    if palavra == self.lst_EntidadesNomeadas[j].palavra:
                        self.lst_EntidadesNomeadas.remove(
                            self.lst_EntidadesNomeadas[j])
                        existe_palavra = 1  # a palavra foi encontrada
                        break  # sai do loop e vai testar a condicao while

    def RemoverPalavrasDuplicadas_entidadesNomeadas(self):

        continuar = 0
        x = 0
        while continuar == 0:
            palavra = self.lst_EntidadesNomeadas[x].palavra

            finalizou = 0
            while finalizou == 0:
                finalizou = 1
                total_palavras = len(self.lst_EntidadesNomeadas)
                for y in range(0, total_palavras):
                    if y != x:  # evita apagar a palavra a ser pesquisada
                        if palavra == self.lst_EntidadesNomeadas[y].palavra:
                            finalizou = 0
                            # verifica se o segundo nome esta vazio.
                            if self.lst_EntidadesNomeadas[x].posterior == "":
                                self.lst_EntidadesNomeadas[x].posterior = self.lst_EntidadesNomeadas[
                                    y].posterior  # tenta colocar o segundo nome da ocorrencia a ser apagada

                            self.lst_EntidadesNomeadas.remove(
                                self.lst_EntidadesNomeadas[y])
                            break

            x = x + 1
            total_palavras = len(self.lst_EntidadesNomeadas)
            if x == total_palavras:
                break  # sai do laço

    def RemoverPalavrasDuplicadas_substantivos(self):

        continuar = 0
        x = 0
        while continuar == 0:
            palavra = lst_substantivosValidos[x].palavra

            finalizou = 0
            while finalizou == 0:
                finalizou = 1
                total_palavras = len(lst_substantivosValidos)
                for y in range(0, total_palavras):
                    if y != x:  # evita apagar a palavra a ser pesquisada
                        if palavra == lst_substantivosValidos[y].palavra:
                            finalizou = 0
                            lst_substantivosValidos.remove(
                                lst_substantivosValidos[y])
                            break

            x = x + 1
            total_palavras = len(lst_substantivosValidos)
            if x == total_palavras:
                break  # sai do laço

    # ---------------Organizar as palavras em ordem de importância
    def OrganizarTopSubstantivos(self):
        global lst_treetagger
        # organiza as cinco palavras mais importantes do texto
        self.lst_top_substantivos = []
        lst_legenda_titulo = []
        lst_legenda = []
        lst_titulo = []
        lst_frequencia_texto = []
        lst_palavra = []

        self.RemoverPalavrasDuplicadas_substantivos()
        # self.total_entidades = self.ContarNumeroEntidadesNomeadas()
        # print("TOTAL DE ENTIDADES________________________= "+str(self.total_entidades))
        total_palavras = len(lst_substantivosValidos)

        for x in range(0, total_palavras):  # para cada palavra

            if lst_substantivosValidos[x].palavra in lst_palavra:
                continue

            # ----------------------- Verifica se está em titulo,legenda,etc e Coloca nos lists
            # pega somente palavras com 2 ou mais ocorrencias no texto
            if lst_substantivosValidos[x].ocorrencias >= 1:
                if lst_substantivosValidos[x].presente_legenda == 1 and lst_substantivosValidos[x].presente_titulo:
                    lst_legenda_titulo.append(lst_substantivosValidos[x])
                # lst_palavra.append(lst_substantivosValidos[x].palavra)

                elif lst_substantivosValidos[x].presente_legenda == 1:
                    lst_legenda.append(lst_substantivosValidos[x])
                # lst_palavra.append(lst_substantivosValidos[x].palavra)

                elif lst_substantivosValidos[x].presente_titulo == 1:
                    lst_titulo.append(lst_substantivosValidos[x])
                #  lst_palavra.append(lst_substantivosValidos[x].palavra)

                elif lst_substantivosValidos[x].ocorrencias >= 1:
                    lst_frequencia_texto.append(lst_substantivosValidos[x])
                #  lst_palavra.append(lst_substantivosValidos[x].palavra)

        contador = 0
        tamanho_lista = 1  # inicia padrão para usar o while
        max_value = len(lst_legenda_titulo)
        count = 0
        while count < max_value and tamanho_lista > 0:  # ESVAZIA A LISTA
            # pega o tamanho da lista atual
            tamanho_lista = len(lst_legenda_titulo)
            maior_frequencia = -1  # variavel
            indice_palavra = -1  # variavel
            for x in range(0, tamanho_lista):  # varre a lista de legenda titulo
                # obtem a maior frequencia e seu indice
                if lst_legenda_titulo[x].ocorrencias > maior_frequencia:
                    maior_frequencia = lst_legenda_titulo[x].ocorrencias
                    indice_palavra = x;
            if tamanho_lista > 0:
                # coloca no top 5
                lst_palavra.append(lst_legenda_titulo[indice_palavra].palavra)
                # remove da lista a palavra já utilizada
                lst_legenda_titulo.remove(lst_legenda_titulo[indice_palavra])
                count = count + 1  # incrementa o contador do top 5
                tamanho_lista = tamanho_lista - 1
                contador = contador + 1
        # ---------------------------------------------- WHile para presente na legenda
        tamanho_lista = 1  # inicia padrão para usar o while
        max_value = len(lst_legenda)
        count = 0
        while count < max_value and tamanho_lista > 0:
            tamanho_lista = len(lst_legenda)  # pega o tamanho da lista atual
            maior_frequencia = -1  # variavel
            indice_palavra = -1  # variavel
            for x in range(0, tamanho_lista):  # varre a lista de legenda titulo
                # obtem a maior frequencia e seu indice
                if lst_legenda[x].ocorrencias > maior_frequencia:
                    maior_frequencia = lst_legenda[x].ocorrencias
                    indice_palavra = x;
            if tamanho_lista > 0:
                # coloca no top 5
                lst_palavra.append(lst_legenda[indice_palavra].palavra)
                # remove da lista a palavra já utilizada
                lst_legenda.remove(lst_legenda[indice_palavra])
                count = count + 1  # incrementa o contador do top 5
                tamanho_lista = tamanho_lista - 1
                contador = contador + 1

        tamanho_lista = 1  # inicia padrão para usar o while
        max_value = len(lst_titulo)
        count = 0
        while count < max_value and tamanho_lista > 0:
            tamanho_lista = len(lst_titulo)  # pega o tamanho da lista atual
            maior_frequencia = -1  # variavel
            indice_palavra = -1  # variavel
            for x in range(0, tamanho_lista):  # varre a lista de legenda titulo
                # obtem a maior frequencia e seu indice
                if lst_titulo[x].ocorrencias > maior_frequencia:
                    maior_frequencia = lst_titulo[x].ocorrencias
                    indice_palavra = x;
            if tamanho_lista > 0:
                # coloca no top 5
                lst_palavra.append(lst_titulo[indice_palavra].palavra)
                # remove da lista a palavra já utilizada
                lst_titulo.remove(lst_titulo[indice_palavra])
                count = count + 1  # incrementa o contador do top 5
                tamanho_lista = tamanho_lista - 1
                contador = contador + 1

        # -------------------------while para ocorrencias---------------------
        tamanho_lista = 1  # inicia padrão para usar o while
        max_value = len(lst_frequencia_texto)
        count = 0
        while count < max_value and tamanho_lista > 0:
            # pega o tamanho da lista atual
            tamanho_lista = len(lst_frequencia_texto)
            maior_frequencia = -1  # variavel
            indice_palavra = -1  # variavel
            for x in range(0, tamanho_lista):  # varre a lista de legenda titulo
                # obtem a maior frequencia e seu indice
                if lst_frequencia_texto[x].ocorrencias > maior_frequencia:
                    maior_frequencia = lst_frequencia_texto[x].ocorrencias
                    indice_palavra = x;
            if tamanho_lista > 0:
                # coloca no top 5
                lst_palavra.append(
                    lst_frequencia_texto[indice_palavra].palavra)
                lst_frequencia_texto.remove(
                    lst_frequencia_texto[indice_palavra])  # remove da lista a palavra já utilizada
                count = count + 1  # incrementa o contador do top 5
                tamanho_lista = tamanho_lista - 1
                contador = contador + 1

        # ---ADICIONA PALAVRAS DO TITULO SE NAO EXISTIREM NO LST_PALAVRA
        print(self.titulo)
        lst_treetagger_titulo = self.tree_tagger.tag(self.titulo)
        if [''] in lst_treetagger_titulo:
            lst_treetagger_titulo.remove([''])
        lst_treetagger += lst_treetagger_titulo
        for x in range(0, len(lst_treetagger_titulo)):

            word_filtrada = lst_treetagger_titulo[x][2]
            lema = lst_treetagger_titulo[x][2]

            print(lema)
            retorno = self.FiltrarSubstantivos(lst_treetagger_titulo[x])
            if retorno == 1:
                palavra_fisica = self.DescobrirPalavraFisica(
                    word_filtrada,
                    self.tipo_wordNet)  # descobre se a palavra é fisica a partir do tipo desejado(physical_entity,object)
            # se for substantivo,palavra fisica(segundo wordNet), e NÃO for nem localizacao e nem organizacao ->coloca no list
            if retorno == 1 and palavra_fisica == 1:
                if word_filtrada not in lst_palavra:
                    lst_palavra.append(word_filtrada)

        # ---ADICIONA PALAVRAS DA LEGENDA SE NAO EXISTIREM NO LST_PALAVRA
        lst_treetagger_legenda = self.tree_tagger.tag(self.legenda)
        if [''] in lst_treetagger_legenda:
            lst_treetagger_legenda.remove([''])
        lst_treetagger += lst_treetagger_legenda
        if len(lst_treetagger_legenda) < 1:

            for x in range(0, len(lst_treetagger_legenda)):

                word_filtrada = lst_treetagger_legenda[x][2]
                retorno = self.FiltrarSubstantivos(lst_treetagger_legenda[x])
                if retorno == 1:
                    palavra_fisica = self.DescobrirPalavraFisica(
                        word_filtrada,
                        self.tipo_wordNet)  # descobre se a palavra é fisica a partir do tipo desejado(physical_entity,object)
                # se for substantivo,palavra fisica(segundo wordNet), e NÃO for nem localizacao e nem organizacao ->coloca no list
                if retorno == 1 and palavra_fisica == 1:
                    if word_filtrada not in lst_palavra:
                        lst_palavra.append(word_filtrada)

        if self.tipo_wordNet == "physical_entity.n.01":
            self.lst_top_substantivos_physical = lst_palavra
        elif self.tipo_wordNet == "object.n.01":
            self.lst_top_substantivos_objects = lst_palavra

    def InterseccaoListasSubstantivos(self):
        lst_palavras_fisicas = []
        lst_palavras_objetos = []
        for pysical in self.lst_top_substantivos_physical:
            lst_palavras_fisicas.append(pysical)
        for object in self.lst_top_substantivos_objects:
            lst_palavras_objetos.append(object)
        lst_interseccao = [
            val for val in lst_palavras_fisicas if val in lst_palavras_objetos]
        self.lst_interseccao_entidades = lst_interseccao  # coloca na variavel global

    def DiferencaListasSubstantivos(self):
        lst_palavras_fisicas = []
        lst_palavras_objetos = []
        for pysical in self.lst_top_substantivos_physical:
            lst_palavras_fisicas.append(pysical)
        for objects in self.lst_top_substantivos_objects:
            lst_palavras_objetos.append(pysical)
        lst_diferencas_fisicas = [
            val for val in lst_palavras_fisicas if val not in lst_palavras_objetos]
        lst_diferencas_objects = [
            val for val in lst_palavras_objetos if val not in lst_palavras_fisicas]
        self.lst_diferenca_entidades = list(set().union(lst_diferencas_fisicas,
                                                        lst_diferencas_objects))  # coloca na variavel global

    def OrganizarTopEntidadesNomeadas(self):
        # organiza as cinco palavras mais importantes do texto

        lst_legenda_titulo = []
        lst_legenda = []
        lst_titulo = []
        lst_frequencia_texto = []
        lst_palavra = []

        total_palavras = len(self.lst_EntidadesNomeadas)

        for x in range(0, total_palavras):  # para cada palavra
            # ----------------------- Verifica se está em titulo,legenda,etc e Coloca nos lists
            if self.lst_EntidadesNomeadas[x].presente_legenda == 1 and self.lst_EntidadesNomeadas[
                x].presente_titulo == 1:
                lst_legenda_titulo.append(self.lst_EntidadesNomeadas[x])
                lst_palavra.append(self.lst_EntidadesNomeadas[x].palavra)
            elif self.lst_EntidadesNomeadas[x].presente_legenda == 1:
                lst_legenda.append(self.lst_EntidadesNomeadas[x])
                lst_palavra.append(self.lst_EntidadesNomeadas[x].palavra)
            elif self.lst_EntidadesNomeadas[x].presente_titulo == 1:
                lst_titulo.append(self.lst_EntidadesNomeadas[x])
                lst_palavra.append(self.lst_EntidadesNomeadas[x].palavra)
            else:
                if self.lst_EntidadesNomeadas[x].ocorrencias > 2:
                    lst_frequencia_texto.append(self.lst_EntidadesNomeadas[x])
                    lst_palavra.append(self.lst_EntidadesNomeadas[x].palavra)

        # ---------------------Seleciona as palavras mais classificadas
        contador = 0
        count = 0

        tamanho_lista = 1  # inicia padrão para usar o while
        max_value = len(lst_legenda_titulo)
        while count < max_value and tamanho_lista > 0:  # ESVAZIA A LISTA
            # pega o tamanho da lista atual
            tamanho_lista = len(lst_legenda_titulo)
            maior_frequencia = -1  # variavel
            indice_palavra = -1  # variavel
            for x in range(0, tamanho_lista):  # varre a lista de legenda titulo
                # obtem a maior frequencia e seu indice
                if lst_legenda_titulo[x].ocorrencias > maior_frequencia:
                    maior_frequencia = lst_legenda_titulo[x].ocorrencias
                    indice_palavra = x
            if tamanho_lista > 0:
                self.lst_top_entidades_nomeadas.append(
                    lst_legenda_titulo[indice_palavra])  # coloca no top 5
                # remove da lista a palavra já utilizada
                lst_legenda_titulo.remove(lst_legenda_titulo[indice_palavra])
                count = count + 1  # incrementa o contador do top 5
                tamanho_lista = tamanho_lista - 1
                contador = contador + 1
            # ---------------------------------------------- WHile para presente na legenda
        tamanho_lista = 1  # inicia padrão para usar o while
        max_value = len(lst_legenda)
        count = 0
        while count < max_value and tamanho_lista > 0:
            tamanho_lista = len(lst_legenda)  # pega o tamanho da lista atual
            maior_frequencia = -1  # variavel
            indice_palavra = -1  # variavel
            for x in range(0, tamanho_lista):  # varre a lista de legenda titulo
                # obtem a maior frequencia e seu indice
                if lst_legenda[x].ocorrencias > maior_frequencia:
                    maior_frequencia = lst_legenda[x].ocorrencias
                    indice_palavra = x
            if tamanho_lista > 0:
                self.lst_top_entidades_nomeadas.append(
                    lst_legenda[indice_palavra])  # coloca no top 5
                # remove da lista a palavra já utilizada
                lst_legenda.remove(lst_legenda[indice_palavra])
                count = count + 1  # incrementa o contador do top 5
                tamanho_lista = tamanho_lista - 1
                contador = contador + 1
        # while para ocorrencias
        tamanho_lista = 1  # inicia padrão para usar o while
        max_value = len(lst_frequencia_texto)
        count = 0
        while count < max_value and tamanho_lista > 0:
            # pega o tamanho da lista atual
            tamanho_lista = len(lst_frequencia_texto)
            maior_frequencia = -1  # variavel
            indice_palavra = -1  # variavel
            for x in range(0, tamanho_lista):  # varre a lista de legenda titulo
                # obtem a maior frequencia e seu indice
                if lst_frequencia_texto[x].ocorrencias > maior_frequencia:
                    maior_frequencia = lst_frequencia_texto[x].ocorrencias
                    indice_palavra = x
            if tamanho_lista > 0:
                self.lst_top_entidades_nomeadas.append(
                    lst_frequencia_texto[indice_palavra])  # coloca no top 5
                # remove da lista a palavra já utilizada
                lst_frequencia_texto.remove(
                    lst_frequencia_texto[indice_palavra])
                count = count + 1  # incrementa o contador do top 5
                tamanho_lista = tamanho_lista - 1
                contador = contador + 1

    def DescobrirPalavraFisica(self, palavra, tipo):

        lst = wn.synsets(palavra, pos=wn.NOUN)
        hyper = lambda s: s.hypernyms()
        for j in range(0, len(lst)):
            synset = str(lst[j])
            synset = synset.replace("Synset('", "")
            synset = synset.replace("')", "")
            # print(synset + " ----" + wn.synset(synset).definition())
            word = wn.synset(synset)
            lista_hierarquia = list(word.closure(hyper))
            for w in range(0, len(lista_hierarquia)):
                synset = str(lista_hierarquia[w])
                synset = synset.replace("Synset('", "")
                synset = synset.replace("')", "")
                # print("("+palavra+")"+synset)
                if synset == "location.n.01":
                    return 0
                if tipo == "physical_entity.n.01":  # busca somente esse tipo
                    if synset == "physical_entity.n.01":
                        return 1
                elif tipo == "object.n.01":  # busca somente esse tipo
                    if synset == "object.n.01":
                        return 1

        return 0

    def entidades_legenda(self):
        """ Retorna as entidades nomeadas presentes na legenda da notícia"""
        lst_entidades = trazer_entidades_nomeadas_v(self.legenda)
        return lst_entidades

    def get_list_top_entidades_nomeadas(self):

        return self.lst_top_entidades_nomeadas

    def delete_blank_words(self):
        global lst_treetagger
        if [''] in lst_treetagger:
            lst_treetagger.remove([''])
