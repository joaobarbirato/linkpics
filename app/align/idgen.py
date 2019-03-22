"""
    Image Description Generator
    @author: João Gabriel Melo Barbirato
"""
import nltk
from app.UTIL import wrapper
from itertools import combinations


class Generator:
    def __init__(self, title, sub, text, aligned_subs):
        self._title = title.replace(".", ". ").replace("  ", " ")
        self._sub = sub.replace(".", ". ").replace("  ", " ")
        self._text = text.replace(".", ". ").replace("  ", " ")
        self._snts = []
        self._snts = nltk.sent_tokenize(text=self._text) + nltk.sent_tokenize(text=self._sub) + \
                     nltk.sent_tokenize(text=self._title)
        self._gen_descr = []
        self._amr_list = []
        self._aligned_subs = aligned_subs

    def _two_match_gen(self):
        """
        Generate descriptions by finding two aligned terms in a single sentence
        :return: Boolean value whether or not it matches the criteria
        """
        self._snts_to_amr()
        _worked = False
        if self._amr_list:
            for amr in self._amr_list:
                for pair in combinations(self._aligned_subs, r=2):
                    if amr.is_node(pair[0]) and amr.is_node(pair[1]):
                        _worked = True
                        if amr.snt not in self._gen_descr:
                            self._gen_descr.append(amr.snt)

        return _worked

    def _summarizing_gen(self, max_tokens=10):
        """
        Generate description by summarizing self._text, resulting on a summarized description with an
        aligned term.
        :return: Boolean value whether or not it matches the criteria
        """
        _MAX_NUM_TOKENS = max_tokens
        _stopwords = nltk.corpus.stopwords.words('english')
        word_frequencies = {}
        snt_scores = {}
        for word in nltk.word_tokenize(self._snts):
            if word not in _stopwords:
                if word not in word_frequencies.keys():
                    word_frequencies[word] = 1
                else:
                    word_frequencies[word] += 1

        max_wfreq = max(word_frequencies.values())
        for word in word_frequencies.keys():
            word_frequencies[word] = word_frequencies[word]/max_wfreq

        for snt in self._snts:
            for word in nltk.word_tokenize(snt.lower()):
                if len(snt.split(' ')) < _MAX_NUM_TOKENS:
                    if snt not in snt_scores.keys():
                        snt_scores[snt] = word_frequencies[word]
                        snt_scores[snt] = word_frequencies[word]

        summary_descr = max(snt_scores, key=snt_scores.get)
        _worked = False
        for sub in self._aligned_subs:
            if sub in summary_descr:
                _worked = True
                self._gen_descr.append(
                    summary_descr
                )

        return _worked

    def _apply_criteria(self, crit_type=None):
        """
        Criteria for confirming description
        :arg crit_type: which criteria
        :return: Boolean value whether or not it matches the criteria
        """
        _worked = False
        if crit_type is not None:
            # match 2 AMR entities
            if crit_type.upper() == "2-MATCH":
                _worked = self._two_match_gen()
            elif crit_type.upper() == "SUMMARIZING":
                _worked = self._summarizing_gen()

        return _worked

    def _snts_to_amr(self):
        """
        Transform natural language sentences to an AMR graph
        :return: an AMR object
        """
        if self._snts is not None and len(self._snts) >= 1:
            import os
            _old_path = os.path.dirname(os.path.abspath(__file__))
            os.chdir(_old_path+'/../amr')
            self._amr_list = wrapper.parse_to_amr_list(snts=self._snts)
            self._amr_list = list(set(self._amr_list))
            os.chdir(_old_path + '/../../')

    def generate_descriptions(self, type="2-MATCH"):
        if self._apply_criteria(crit_type=type.replace(" ", "")):
            print("[IDG] Success!")
            return True
        else:
            print("[IDG] No img description generated :(")
            return False

    def get_gen_descr(self):
        return self._gen_descr
