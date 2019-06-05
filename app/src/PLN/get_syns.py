# -*- coding: utf-8 -*-
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import Synset

"""
    Autor: Joao Gabriel Melo Barbirato
    Objetivo: obter palavras sinônimas a fim de alinhá-las (n:1)
"""


def get_syns(word=None):
    """
    Obtain synonyms of a word in order to perform a n:1 alignment
    :param word: target word
    :return: a list containing the best candidates for synonyms of targeted word
    """
    WUP_SYN_THR = 0.63

    def _is_similar(obj1, obj2):
        """
        Determine whether or not two Synset objects are similar using WUP similarity and the WUP_SYN_THR threshold
        :param obj1: First Synset object
        :param obj2: Second Synset object
        :return: boolean True if is greater than the threshold, False otherwise
        """
        if isinstance(obj1, Synset) and isinstance(obj2, Synset):
            similarity = wn.wup_similarity(obj1, obj2)
            return similarity > WUP_SYN_THR if similarity is not None else False

    target_synset = wn.synsets(word, pos=wn.NOUN)[0]  # first is always the searched word
    candidate_synsets = [(lemma, wn.synsets(lemma)[0]) for lemma in target_synset.lemma_names()[1:]]
    best_candidates = []
    for lemma, ss in candidate_synsets:
        if _is_similar(target_synset, ss):
            best_candidates.append(lemma.replace('_', ' '))

    # Make sure that there's no redundancy
    if word in best_candidates:
        best_candidates.remove(word)

    return best_candidates
