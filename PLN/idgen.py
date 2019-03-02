"""
    Image Description Generator
    @author: João Gabriel Melo Barbirato
"""
import nltk
from amr.wrapper import parse_to_amr_list
from itertools import combinations


class Generator:
    def __init__(self, title, sub, text, aligned_subs):
        self._title = title
        self._sub = sub
        self._text = text
        self._snts = []
        self._snts = nltk.sent_tokenize(text=self._text) + nltk.sent_tokenize(text=self._sub) + nltk.sent_tokenize(text=self._title)
        self._gen_descr = []
        self._amr_list = []
        self._aligned_subs = aligned_subs

    def _apply_criteria(self, crit_type=None):
        """
        Criteria for confirming description
        :arg crit_type: which criteria
        :return: Boolean value whether or not it matches the criteria
        """
        _worked = False
        if crit_type is not None and self._amr_list:
            # match 2 AMR entities
            if crit_type.upper() == "2-MATCH":
                for amr in self._amr_list:
                    for pair in combinations(self._aligned_subs, r=2):
                        if amr.is_node(pair[0]) and amr.is_node(pair[1]):
                            _worked = True
                            self._gen_descr.append(
                                self._snts[self._amr_list.index(amr)]
                            )

        return _worked

    def _snts_to_amr(self):
        """
        Transform natural language sentences to an AMR graph
        :return: an AMR object
        """
        if self._snts is not None and len(self._snts) >= 1:
            self._amr_list = parse_to_amr_list(snts=self._snts)

    def generate_descriptions(self):
        self._snts_to_amr()
        if self._apply_criteria(crit_type="2-MATCH"):
            print("[IDG] Success!")
            return True
        else:
            print("[IDG] No img description generated :(")
            return False

    def get_gen_descr(self):
        return self._gen_descr

    pass
