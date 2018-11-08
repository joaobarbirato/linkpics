# -*- coding: utf-8 -*-
from word_embeddings import WordEmbeding as we

"""
    Autor: Joao Gabriel Melo Barbirato
    Objetivo: obter palavras sinônimas a fim de alinhá-las (n:1)
"""

def get_syns(word=None):
    THR = 50
    words = []
    distances = []
    best_w = []
    
    # find related words
    for ss in wn.synsets(word):
        for name in ss.lemma_names()[1:]:   # firs is always the searched word
            if name not in words:
                words.append(name)

    we.CarregarWordEmbeddings()
    vec_word = we.RetornarVetor(word)
    for w in words:
        distance_we = 0
        vec_w = we.RetornarVetor(w)
        for x in range(0,100):
            distance_we += abs(vec_word[x] - vec_w[x])
        distances.append(distance_we)
    
    for i in range(len(words)):
        if distances[i] <= THR:
            best_w.append(words[i])
    
    return best_w
