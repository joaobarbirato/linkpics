from math import log2, sqrt

import nltk
from nltk.chunk.regexp import ChunkRule

"""
    Autor: Joao Gabriel Melo Barbirato
    Objetivo: criar um regexparser pra chunking de tags personalizadas no lugar do treetagger
"""


class MWEChunker:
    def __init__(self, lst_treetagger=None):
        """
        MWEChunker constructor
        :param lst_treetagger: list generated by tree-tagger POS tagging method 
        """
        self.MLE_THR = 0.05
        self._list_tt = lst_treetagger

        self._new_list_tt = []
        self._raw_mwes = []
        self._counter = {}

        self.DICE_THR = 0.065
        # Prepositional phrases
        self._pp_rule_set = [
            ChunkRule("<IN><NP>", "PrepPHR")
        ]

        # Noun compounds
        # 2-gram rules
        self._nc_2gram_set = [
            ChunkRule("<NN><NN.?>", descr="(SUB(Plur)?)? (SUB(Plur)?)?"),
            ChunkRule("<JJ><NN.?>", descr="ADJ (SUB(Plur)?)?"),
            ChunkRule("<PPH><NN.?>", descr="AAN (SUB(Plur)?)?"),
            ChunkRule("<NN.?><JJ>", descr="(SUB(Plur)?)? ADJ"),
            ChunkRule("<NN.?><PPH>", descr="(SUB(Plur)?)? AAN")
        ]

        # n-gram rules
        self._nc_ngram_set = [
            ChunkRule("(<JJ.?>|<PPH>)+<NN><NN.?>?", descr="(ADJ|PrepPHR)+ SUB SUB?"),
            ChunkRule("<NN><NN.?>(<JJ.?>|<PPH>)*", descr="SUB SUB (ADJ|PrepPHR)*")
        ]

    def set_list_tt(self, list_tt=None):
        """
        Setter for self._list_tt
        :param list_tt: list of tree-tagger POS tagging
        :return: True if this operation was successful, False if it wasn't
        """
        if list_tt is not None and list_tt:
            self._list_tt = list_tt
            return True
        return False

    def filter_mwes(self, metric='dice'):
        print("IN FILTER_MWES")
        print("[_raw_mwes]:", self._raw_mwes)
        _new_raw_mwes = []
        for mwe in self._raw_mwes:
            if (metric == 'dice' and self._dice_coef(ngram=mwe[1]) > self.DICE_THR) | \
                    (metric == 'mle' and self._mle_coef(ngram=mwe[1]) > self.MLE_THR):
                _new_raw_mwes.append(mwe)

        return _new_raw_mwes

    def chunk(self):
        """
        Identify MWEs inside list of tree-tagger POS tagging representation of words
        :return: updated tree-tagger list
        """
        if self._list_tt is not None:
            tree = nltk.Tree('S', [(word, tag) for [word, tag, _] in self._list_tt])
            tree_pp = self._parse_rcp(label='PPH', tree=tree, rule_set=self._pp_rule_set)
            tree_nc = self._parse_rcp(label='NC', tree=tree_pp, rule_set=self._nc_ngram_set)

            _reparsed_tree_nc = nltk.Tree('S', [])
            for rule in self._nc_2gram_set:
                rcp_nc_subtree = nltk.RegexpChunkParser([rule], chunk_label='NC', root_label='NC')
                for child_tree in tree_nc:
                    if isinstance(child_tree, nltk.Tree):
                        reparsed_child_tree = rcp_nc_subtree.parse(child_tree)
                        if reparsed_child_tree != child_tree:
                            if child_tree not in reparsed_child_tree:
                                _reparsed_tree_nc.append(reparsed_child_tree)
                        else:
                            _reparsed_tree_nc.append(child_tree)
                    else:
                        if child_tree not in _reparsed_tree_nc:
                            _reparsed_tree_nc.append(child_tree)

            self._new_list_tt, nc_saving_list = self._tree_to_treetaggerlist(tree=_reparsed_tree_nc)
            unnested_nc_saving_list = self._unnest_mwes(nc_saving_list)
            # print("[list_tt]: ", self._list_tt)
            # print("[_new_list_tt]: ", self._new_list_tt)
            self._raw_mwes = self._join_mwes(unnested_nc_saving_list)
            # print("[_unnest_mwes]:", unnested_nc_saving_list)
            self._count_words()
            self._print_measures()
            self._raw_mwes = self.filter_mwes()
            # print("[FILTERED _RAW_MWES]:", self._raw_mwes)
        return self._new_list_tt

    def _tree_to_treetaggerlist(self, tree=None, label=None):
        """
        Recursive algorithm to obtain a tree-tagger representation of nltk.Tree
        :param tree: nltk.Tree object
        :param label: recursive optional param for chunk label
        :return: tree-tagger list version of tree object
        """
        tt_list = []
        nc_list = []
        n_leaves = len(tree.leaves())
        is_mwe = label is not None or label == 'S'
        if tree is not None:
            list_parsed = list(tree)
            word_count = 0
            _nc_save_item = []
            for item in list_parsed:
                if isinstance(item, tuple):
                    _pre_tag = ''
                    if is_mwe:
                        _pre_tag = '%s_' % label
                        if word_count == 0:
                            _pre_tag += 'b_'
                        elif word_count == n_leaves - 1:
                            _pre_tag += 'o_'
                        else:
                            _pre_tag += 'i_'
                    new_node = [
                        item[0],
                        _pre_tag + item[1],
                        self._get_lemma_from_word(word=item[0])
                    ]
                    tt_list.append(new_node)
                    if is_mwe:
                        nc_list.append([new_node[0], new_node[2]])
                elif isinstance(item, nltk.Tree):
                    result = self._tree_to_treetaggerlist(
                        tree=item,
                        label=label + '_' + item.label() if is_mwe else item.label()
                    )
                    tt_list += result[0]
                    nc_list.append(result[1])

                word_count += 1
            if _nc_save_item:
                nc_list.append(_nc_save_item)

        return tt_list, nc_list

    def _get_lemma_from_word(self, word=None):
        """
        Find lemmatized version of a given word based on tree-tagger POS tagging list
        :param word: given word
        :return: lemma
        """
        if word is not None:
            for [w, _, l] in self._list_tt:
                if word == w:
                    return l

    def _unnest_list(self, nested_list=None):
        """
        Recursive function for transforming a given nested list into an unnested
        :param nested_list: list of list which contains lists
        :return: unnest version of nested list
        """
        if nested_list is not None and nested_list:
            unnested_list = []
            for item in nested_list:
                if isinstance(item[0], list):
                    if any(isinstance(i[0], list) for i in item):
                        # it's a nested list of nested lists
                        unnested_list += self._unnest_list(nested_list=item)
                    else:
                        nested_nc = [i for i in item]
                        unnested_list += nested_nc

                elif isinstance(item[0], str):
                    unnested_list.append(item)
            return unnested_list

    def _unnest_mwes(self, mwe_list=None):
        """
        Transform nested MWE list into an unnest version
        :param mwe_list: given MWE list
        :return: a new unnest version of the given list
        """
        if mwe_list is not None and mwe_list:
            new_list = []
            for nc in mwe_list:
                if any(isinstance(item[0], list) for item in nc):
                    new_nc = self._unnest_list(nc)
                    if new_nc not in new_list:
                        new_list.append(new_nc)
                elif all(isinstance(item[0], str) for item in nc):
                    if nc not in new_list:
                        new_list.append(nc)

            return new_list

    def has_mwe(self):
        """
        Inform if this chunker has found any MWE
        :return: True if it has, False if it hasn't
        """
        return False if not self._raw_mwes else True

    def get_mwes_from_aligned(self, word=None):
        """
        Find all MWEs which contains a given aligned word
        :param word: aligned word
        :return: a list of MWEs which contains the aligned word
        """
        res = []
        found = False
        if word:
            for (mwe, lemma_mwe) in self._raw_mwes:
                if word in lemma_mwe.split(' '):
                    found = True
                    res.append(mwe)

        return res if found else found

    @staticmethod
    def _join_mwes(unnest_list=None):
        """
        Join word-lemma lists of an MWE into a single tuple (n-gram, lemmas)
        :param unnest_list: given list of MWE lists
        :return: new list of tuples (n-gram, lemmas)
        """
        if unnest_list is not None and unnest_list:
            joined_list = []
            for nc in unnest_list:
                word_buffer = ''
                lemma_buffer = ''
                for word_lemma in nc:
                    word_buffer += word_lemma[0] + ' '
                    lemma_buffer += word_lemma[1] + ' '

                word_buffer = word_buffer[:-1]
                lemma_buffer = lemma_buffer[:-1]
                joined_list.append((word_buffer, lemma_buffer))

            return joined_list

    @staticmethod
    def _parse_rcp(label=None, tree=None, rule_set=None):
        """
        Parse a given tree with nltk.RegexpChunkParser to chunk compounds based on given RegExp rules
        :param label: POS tag of the new chunk
        :param tree: tree to identify chunks
        :param rule_set: nltk.ChunkRules for RegExp identification
        :return: parsed tree with chunks
        """
        if (label and tree and rule_set) is not None:
            rcp = nltk.RegexpChunkParser(rules=rule_set, chunk_label=label)
            return rcp.parse(tree)

    def _add_counter_dict(self, item, occ=1):
        if self._counter and item in self._counter:
            self._counter[item] += occ
        else:
            self._counter[item] = occ

    def _get_word_counter(self, item):
        if item in self._counter:
            return self._counter[item]
        return 0

    def _count_words(self):
        for item in self._list_tt:
            lemma = item[2]
            self._add_counter_dict(lemma)

    def _get_ngram_count(self, ngram=('', ''), add_dict=False):
        """
        Count how many times a n-gram appears in text
        :param ngram: tuple (n-gram, lemmatized n-gram)
        :param add_dict: Boolean for dictionary registration (or not)
        :return:
        """
        ngram_split = ngram.split()
        len_ngram = len(ngram_split)
        len_list_tt = len(self._list_tt)
        count = 0
        for i in range(0, len_list_tt):
            lemma_list_tt_slice = [item[2] for item in self._list_tt[i:len_ngram + i]]
            if lemma_list_tt_slice == ngram_split:
                count += 1

        if add_dict:
            self._add_counter_dict(ngram, occ=count)

        return count

    def _expected_value(self, ngram):
        """
        Statistical expected value for n-grams
        :param ngram: identified MWE
        :return: expected value of a given MWE
        """
        n = len(ngram.split())
        N = len(self._new_list_tt)
        return 1 / (N ** (n - 1))

    def _dice_coef(self, ngram):
        """

        :param ngram:
        :return:
        """
        dice = len(ngram.split()) * self._get_ngram_count(ngram) / (
            sum([self._get_word_counter(word) for word in ngram.split()]))
        print("dice(%r) = %f" % (ngram, dice))
        return dice

    def _mle_coef(self, ngram):
        """

        :param ngram:
        :return:
        """
        mle = self._get_ngram_count(ngram) / len(self._new_list_tt)
        return mle

    def _pmi_coef(self, ngram):
        """

        :param ngram:
        :return:
        """
        try:
            pmi = log2(self._get_ngram_count(ngram) / self._expected_value(ngram))
            return pmi
        except ValueError:
            return -1
        except ZeroDivisionError:
            return -1

    def _t_score(self, ngram):
        """

        :param ngram:
        :return:
        """
        c = self._get_ngram_count(ngram)
        try:
            t_score = (c - self._expected_value(ngram)) / sqrt(c)
            return t_score
        except ZeroDivisionError:
            return -1

    def _print_measures(self):
        for mwe in self._raw_mwes:
            print("dice[%r] = %f\nmle[%r] = %f\npmi[%r] = %f\nt_score[%r] = %f" %
                  (mwe[1], self._dice_coef(mwe[1]), mwe[1], self._mle_coef(mwe[1]),
                   mwe[1], self._pmi_coef(mwe[1]), mwe[1], self._t_score(mwe[1])))
            print()
