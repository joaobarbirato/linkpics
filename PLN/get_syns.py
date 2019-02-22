# -*- coding: utf-8 -*-
from .word_embeddings import WordEmbeding
from nltk.corpus import wordnet as wn

"""
    Autor: Joao Gabriel Melo Barbirato
    Objetivo: obter palavras sinônimas a fim de alinhá-las (n:1)
"""


def get_syns(word=None):
    THR = 50
    words = []
    distances = []
    best_w = []

    try:
        # find related words
        for ss in wn.synsets(word, pos=wn.NOUN):
            for name in ss.lemma_names()[1:]:  # first is always the searched word
                if name not in words:
                    words.append(name)

        we = WordEmbeding(100)

        we.CarregarWordEmbeddings()
        vec_word = we.RetornarVetor(word)
        n_vecw_none = 0
        if words is not None:
            for w in words:
                distance_we = 0
                vec_w = we.RetornarVetor(w)
                if vec_w is not None:
                    for x in range(0, 100):
                        distance_we += abs(vec_word[x] - vec_w[x])
                    distances.append(distance_we)
                else:
                    n_vecw_none += 1

            for i in range(len(words) - n_vecw_none):
                if distances[i] <= THR:
                    best_w.append(words[i])
    except Exception as e:
        pass

    return best_w
