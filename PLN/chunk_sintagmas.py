import nltk
from nltk.stem import WordNetLemmatizer

"""
    Autor: Joao Gabriel Melo Barbirato
    Objetivo: criar um regexparser pra chunking de tags personalizadas no lugar do treetagger
"""

__CHUNK_NAME = "MWE"

# (ADVERBIO?|ADJETIVO?|VERBO?)* NOME NOME? (brown fox, lazy dog, volleyball champion)
# Noun compounds (http://aim-west.imag.fr/what-are-mwes/):
__CHUNK_GRAM = r""+__CHUNK_NAME + \
                ": {<RB.?>*<JJ.?>*<VB.?>*<NN><NN.?>|" \
                "<NN><NN.?>*<RB.?>*<JJ.?>*<VB.?>*}"


def chunk(lst_tree_tagger=None):
    lemmatizer = WordNetLemmatizer()
    parser = nltk.RegexpParser(__CHUNK_GRAM)
    if lst_tree_tagger is not None:
        return_list = []
        word_buffer = ""
        lemma_buffer = ""
        buffer_mode = False

        # transformar a saída do TreeTagger.tag()
        tagged = [(word, tag) for [word, tag, _] in lst_tree_tagger]

        # Aplicar chunk
        tree = parser.parse(tagged).pos()

        # Restaurar a saída do TreeTagger com o(s) novo(s) chunks
        for ((word, tag), chunk) in tree:
            if chunk == "S":
                if buffer_mode:
                    return_list.append([word_buffer[:-1], __CHUNK_NAME, lemma_buffer[:-1]])
                    word_buffer = ""
                    lemma_buffer = ""
                    buffer_mode = False

                return_list.append([word, tag, lemmatizer.lemmatize(word)])

            elif chunk == __CHUNK_NAME:
                buffer_mode = True
                word_buffer += word + " "
                lemma_buffer += lemmatizer.lemmatize(word) + " "
        return return_list
