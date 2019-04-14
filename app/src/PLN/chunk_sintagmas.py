import nltk

"""
    Autor: Joao Gabriel Melo Barbirato
    Objetivo: criar um regexparser pra chunking de tags personalizadas no lugar do treetagger
"""

__CHUNK_NAME = "MWE"

# (ADVERBIO?|ADJETIVO?|VERBO?)* NOME NOME? (brown fox, lazy dog, volleyball champion)
# Noun compounds (http://aim-west.imag.fr/what-are-mwes/):
__CHUNK_GRAM = r"" + __CHUNK_NAME + \
               ": {(<RB.?>|<JJ.?>|<VB.?>)+<NN><NN.?>?|" \
               "(<RB.?>|<JJ.?>|<VB.?>)*<NN><NN.?>|" \
               "<NN>(<NN.?>|<RB.?>|<JJ.?>|<VB.?>)+}"


def chunk(lst_tree_tagger=None):

    def _get_lemma_from_word(word=None):
        if word is not None:
            for [w, _, l] in lst_tree_tagger:
                if word == w:
                    return l

    def _get_pos_from_word(word=None):
        if word is not None:
            for [w, p, _] in lst_tree_tagger:
                if word == w:
                    return p

    parser = nltk.RegexpParser(__CHUNK_GRAM)
    if lst_tree_tagger is not None:
        return_list = []
        chunk_saving_list = []
        word_buffer = ""
        buffer_mode = False

        # transformar a saída do TreeTagger.tag()
        tagged = [(word, tag) for [word, tag, _] in lst_tree_tagger]

        # Aplicar chunk
        tree = parser.parse(tagged).pos()
        mw_size = 0
        # Restaurar a saída do TreeTagger com o(s) novo(s) chunks
        for ((word, tag), chunk) in tree:
            if chunk == "S":
                if buffer_mode:
                    word_buffer = word_buffer.split(' ')[:-1]
                    mw_size = len(word_buffer)
                    # mapear a expressao multi-palavras
                    for i in range(len(word_buffer)):
                        if i == 0:  # primeira palavra
                            pfix_chunk = "_b"
                        elif i == mw_size - 1:  # última palavra
                            pfix_chunk = "_o"
                        else:
                            pfix_chunk = "_i"  # palavras do meio
                        return_list.append([word_buffer[i], _get_pos_from_word(word_buffer[i]) + "_" + __CHUNK_NAME + pfix_chunk,
                                            _get_lemma_from_word(word_buffer[i])])

                    chunk_saving_list.append((word_buffer, [_get_lemma_from_word(w) for w in word_buffer]))
                    print(__CHUNK_NAME, ': ', chunk_saving_list[-1:])
                    word_buffer = ""
                    buffer_mode = False
                    mw_size = 0

                return_list.append([word, tag, _get_lemma_from_word(word)])
            elif chunk == __CHUNK_NAME:
                buffer_mode = True
                word_buffer += word + " "
                mw_size += 1

        return [return_list, chunk_saving_list]
