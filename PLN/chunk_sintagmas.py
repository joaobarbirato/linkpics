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
                ": {(<RB.?>|<JJ.?>|<VB.?>)+<NN><NN.?>?|" \
                "(<RB.?>|<JJ.?>|<VB.?>)*<NN><NN.?>|"     \
                "<NN>(<NN.?>|<RB.?>|<JJ.?>|<VB.?>)+}" 


def chunk(lst_tree_tagger=None):
    lemmatizer = WordNetLemmatizer()
    parser = nltk.RegexpParser(__CHUNK_GRAM)
    if lst_tree_tagger is not None:
        return_list = []
        word_buffer = ""
        buffer_mode = False

        # transformar a saída do TreeTagger.tag()
        tagged = [(word, tag) for [word, tag, _] in lst_tree_tagger]

        # Aplicar chunk
        tree = parser.parse(tagged).pos()

        # Restaurar a saída do TreeTagger com o(s) novo(s) chunks
        for ((word,tag),chunk) in tree:
            if chunk == "S":
                if buffer_mode:
                    word_buffer = word_buffer.split(' ')[:-1]
                    # mapear a expressao multi-palavras
                    for i in range(len(word_buffer)):
                        pfix_chunk = None
                        if i == 0: # primeira palavra
                            pfix_chunk = "_b"
                        elif i == mw_size - 1: # última palavra
                            pfix_chunk = "_o"
                        else:
                            pfix_chunk = "_i" # palavras do meio
                        return_list.append([word_buffer[i], __CHUNK_NAME + pfix_chunk, \
                                           lemmatizer.lemmatize(word_buffer[i])])

                    word_buffer = ""
                    buffer_mode = False
                    
                return_list.append([word, tag, lemmatizer.lemmatize(word)])
            elif chunk == __CHUNK_NAME:
                buffer_mode = True
                word_buffer += word + " "
        return return_list
