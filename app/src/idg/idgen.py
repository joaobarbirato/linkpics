"""
    Image Description Generator
    @author: João Gabriel Melo Barbirato
"""
from operator import methodcaller

from app.amr_module.models import AMRModel, biggest_amr, top_from_triples_list, create_amrmodel
from app.desc_module.models import create_description
from app.model_utils import PrintException
from app.align_module.models import News, Alignment
from app.align_module.base_model import Sentence, sntsmodel_to_amrmodel, create_sentence

from app.src.util.amrtools.wrapper import parse_to_amr_list, penman_to_text


class Generator(object):
    _current_alignment: Alignment

    def __init__(self, news_object):
        """

        :type news_object: News
        :param news_object:
        """
        self.news_object = news_object
        self.amr_models = []
        self._snts_from_alignment = None
        self._current_alignment = None

    def get_generated_descriptions(self):
        return [align.get_description() for align in self.news_object.alignments()]

    def relate_amr(self):
        try:
            amr_list = parse_to_amr_list(snts=self.news_object.get_sentences(return_type="str"))
            zip_amr_sntobj = zip(amr_list, self.news_object.get_sentences())
            sntobj: Sentence
            for amr, sntobj in zip_amr_sntobj:
                amr_model = AMRModel(object=amr.get_penman(return_type='graph'))
                sntobj.add_amr(amr_model)

        except Exception as exc:
            PrintException()

    def generate(self, method='baseline5'):
        """

        :return:
        """
        try:
            all_alignments = self.news_object.alignments()

            descr_to_generate = []

            alignment: Alignment
            for alignment in all_alignments:
                self._snts_from_alignment = alignment.sentences()
                self._current_alignment = alignment
                try:
                    response = self._generate_amr(method=method)
                    if response is not None:
                        generated_amr, main_ancestral, adjacent_ancestral = response
                        descr_to_generate.append((alignment, generated_amr, main_ancestral, adjacent_ancestral))
                except Exception as exc:
                    PrintException()
                    print(f'[{__file__}] Error while generating AMR from {alignment}: {str(exc)}')

            amr_to_generate_text = []
            for alignment, generated_amr, _, _ in descr_to_generate:
                amr_to_generate_text.append(generated_amr)

            _generated_text_list = penman_to_text(amr_list=amr_to_generate_text)
            for ((alignment, generated_amr, main_ancestral, adjacent_ancestral), _generated_text) \
                    in zip(descr_to_generate, _generated_text_list):
                description = create_description(text=_generated_text, method=method)
                description.add_amr(generated_amr)
                main_sentence = create_sentence(copy=main_ancestral.get_sentence())
                main_copy = create_amrmodel(copy=main_ancestral)
                main_sentence.add_amr(main_copy)
                main_sentence.save()
                adj_copies = []
                for aa in adjacent_ancestral:
                    aa_sentence = create_sentence(copy=aa.get_sentence())
                    aa_copy = create_amrmodel(copy=aa)
                    aa_sentence.add_amr(aa_copy)
                    aa_sentence.save()
                    adj_copies.append(aa_copy)
                description.keep_amr(main_copy, adj_copies)
                alignment.add_description(description)

        except Exception as exc:
            PrintException()
            print(f'[{__file__}] Error while generating descriptions: {str(exc)}')

    def _generate_amr(self, method='baseline4'):
        """

        :param method:
        :return:
        """
        try:
            if method == 'baseline4':
                generating_method = self._baseline4()
            elif method == 'baseline5':
                generating_method = self._baseline5()
            else:
                generating_method = None
            return generating_method
        except Exception as exc:
            PrintException()
            print(f'[{__file__}] Error while generating AMR: {str(exc)}')

    def _choose_biggest(self, info_list):
        found = False
        copy_info_list = info_list
        base_info = None
        while not found and copy_info_list:
            biggest_subgraph = biggest_amr([info["subgraph"] for info in copy_info_list])
            base_info = [info for info in copy_info_list if info["subgraph"] == biggest_subgraph][0]
            if self._current_alignment.get_term() == base_info["triple"].target:
                found = True
            copy_info_list.remove(base_info)
        return base_info, copy_info_list

    def _baseline3(self):
        try:
            amr_list = sntsmodel_to_amrmodel(self._snts_from_alignment)
            _big_amr = biggest_amr(amr_list)

            amr_list.remove(_big_amr)
            print(_big_amr)

            _old_big_amr = _big_amr
            for amr in amr_list:
                focus_big_amr = _big_amr.get_triple(relation='instance', target=self._current_alignment.get_term())
                focus_small_amr = amr.get_triple(relation='instance', target=self._current_alignment.get_term())
                if focus_big_amr is not None and focus_small_amr is not None:
                    small_amr_subgraph = amr.get_subgraph(top=focus_small_amr)
                    _big_amr.add(other=small_amr_subgraph, tuple_ref=(focus_big_amr.source, focus_small_amr.source))

            return _big_amr # if _big_amr != _old_big_amr else None
        except Exception as exc:
            PrintException()
            print(f'Error on baseline3: {str(exc)}')

    @staticmethod
    def _add_parent_to_base(info, base):
        if info["parent"]:
            info["parent"][1].invert()
            base["subgraph"].add(
                other=create_amrmodel(triples=base["parent"], top=base["parent"][2].source),
                tuple_ref=(base["triple"].source, base["parent"][2].source))
        return base

    def sentence_selection(self, select=0):
        # alignments only
        if select == 0:
            pass
        # alignments and it's corefs
        elif select == 1:
            pass
        # alignments, corefs and some TODO WordNet relation
        elif select == 2:
            pass
        else:
            return self.sentence_selection(0)

    def _baseline4(self):
        """
        - alignment
        - with parents
        :return:
        """
        try:
            amr_list = sntsmodel_to_amrmodel(self._snts_from_alignment)
            information = []
            amr: AMRModel
            for amr in amr_list:
                is_name = amr.is_name(self._current_alignment.get_term())
                if not is_name:
                    focus_triple = amr.get_triple(relation='instance', target=self._current_alignment.get_term())
                else:
                    focus_triple = is_name
                if focus_triple is not None and focus_triple:
                    focus_subgraph = amr.get_subgraph(top=focus_triple)
                    focus_parent = amr.get_parents(focus_triple)
                    information.append(
                        {
                            "triple": focus_triple,
                            "subgraph": focus_subgraph,
                            "parent": focus_parent,
                            "amr": amr
                        }
                    )

            if information:
                base_info, information = self._choose_biggest(information)
                base_info = self._add_parent_to_base(info=base_info, base=base_info)
                appended_amr_list = []
                if len(information) > 1:
                    for info in information:
                        _before = base_info["subgraph"]
                        base_info["subgraph"].add(other=info["subgraph"],
                                                  tuple_ref=(base_info["triple"].source, info["triple"].source))
                        base_info = self._add_parent_to_base(info=info, base=base_info)

                        if _before != base_info["subgraph"]:
                            appended_amr_list.append(info)

                return base_info["subgraph"], base_info["amr"], [info["amr"] for info in appended_amr_list]
        except Exception as exc:
            PrintException()
            print(f'Error on baseline4: {str(exc)}')

    def _baseline5(self):
        """
        - alignment
        - without parents
        :return:
        """
        try:
            amr_list = sntsmodel_to_amrmodel(self._snts_from_alignment)
            information = []
            amr: AMRModel
            for amr in amr_list:
                is_name = amr.is_name(self._current_alignment.get_term())
                if not is_name:
                    focus_triple = amr.get_triple(relation='instance', target=self._current_alignment.get_term())
                else:
                    focus_triple = is_name
                if focus_triple is not None and focus_triple:
                    focus_subgraph = amr.get_subgraph(top=focus_triple)
                    information.append(
                        {
                            "triple": focus_triple,
                            "subgraph": focus_subgraph,
                            "amr": amr
                        }
                    )

            if information:
                base_info, information = self._choose_biggest(information)
                appended_amr_list = []
                if len(information) > 1:
                    for info in information:
                        _before = base_info["subgraph"]
                        base_info["subgraph"].add(other=info["subgraph"],
                                                  tuple_ref=(base_info["triple"].source, info["triple"].source))

                        if _before != base_info["subgraph"]:
                            appended_amr_list.append(info)

                return base_info["subgraph"], base_info["amr"], [info["amr"] for info in appended_amr_list]
        except Exception as exc:
            PrintException()
            print(f'Error on baseline5: {str(exc)}')

    # def _filter_commons(self, sns, current_alignment=None):
    #     """
    #
    #     :param sns:
    #     :return:
    #     """
    #
    #     """
    #         amrs <- amr_from_sns(sns)
    #         size <- len(amrs)
    #         return_list <- list()
    #         FOR i IN range(2:size):
    #             FOR combination IN COMBINE(amrs, i):
    #                 IF has_common_node(combination):
    #                     return_list.APPEND((combination, node))
    #     """
    #     from sqlalchemy.orm.collections import InstrumentedList
    #     amr_list = InstrumentedList(s.get_amr() for s in sns)
    #     return_list = InstrumentedList()
    #
    #     # while amr_list:
    #     #     amr1 = amr_list.pop()
    #     #     amr2 = amr_list.pop()
    #     #     generated_amr: AMRModel = self._generate_amr(amr1=amr1, amr2=amr2)
    #
    #     amr_combinations = combinations(amr_list, 2)
    #     new_amr_list = amr_list
    #     combination_as_list = list(amr_combinations)
    #     removed = []
    #     while combination_as_list and amr_combinations:
    #         for amr1, amr2 in amr_combinations:
    #             generated_amr: AMRModel = self._generate_amr(amr1=amr1, amr2=amr2, alignment=current_alignment)
    #             if generated_amr is not None:
    #                 return_list.append(generated_amr)
    #                 new_amr_list.append(generated_amr)
    #
    #             removed.append((amr1, amr2))
    #             combination_as_list.remove((amr1, amr2))
    #
    #         amr_combinations = combinations(list(set(new_amr_list) - set(removed)), 2)
    #         combination_as_list = list(amr_combinations)
    #
    #     return return_list


# class Generator:
#     def __init__(self, title, sub, text, aligned_subs):
#         """
#
#         :type aligned_subs: AlignGroup
#         """
#         self._title = title.replace(".", ". ").replace("  ", " ")
#         self._sub = sub.replace(".", ". ").replace("  ", " ")
#         self._text = text.replace(".", ". ").replace("  ", " ")
#         self._snts = []
#         self._snts = nltk.sent_tokenize(text=self._text) + nltk.sent_tokenize(text=self._sub) + \
#                      nltk.sent_tokenize(text=self._title)
#         self._gen_descr = []
#         self._amr_list = []
#         self._aligned_subs = aligned_subs
#
#     def _paint_alignment(self, snt, alignment):
#         if not isinstance(alignment, list):
#             _open_tag = '<b style="color:rgb(' + str(alignment.get_color()) + ');">'
#             _close_tag = '</b>'
#             _pre_char_list = ['(', ' ', '-', '"']
#             painted_snt = snt
#             for pc in _pre_char_list:
#                 painted_snt = painted_snt.replace(pc + alignment, pc + _open_tag + alignment + _close_tag)
#             return painted_snt
#         else:
#             painted_snt = snt
#             for a in alignment:
#                 _open_tag = '<b style="color:rgb(' + str(a.get_color()) + ');">'
#                 _close_tag = '</b>'
#                 _pre_char_list = ['(', ' ', '-', '"']
#                 _snt = ''
#                 for pc in _pre_char_list:
#                     painted_snt = painted_snt.replace(pc + a.term, pc + _open_tag + a.term + _close_tag)
#             return painted_snt
#
#     def _two_match_gen(self):
#         """
#         Generate descriptions by finding two aligned terms in a single sentence
#         :return: Boolean value whether or not it matches the criteria
#         """
#         self._snts_to_amr()
#         _worked = False
#         if self._amr_list:
#             for amr in self._amr_list:
#                 for pair in combinations(self._aligned_subs, r=2):
#                     if amr.is_node(pair[0].term) and amr.is_node(pair[1].term):
#                         _worked = True
#                         if amr.snt not in self._gen_descr:
#                             painted_snt = self._paint_alignment(amr.snt, [pair[0], pair[1]])
#                             self._gen_descr.append(painted_snt)
#
#         return _worked
#
#     def _summarizing_gen(self, max_tokens=10):
#         """
#         Generate description by summarizing self._text, resulting on a summarized description with an
#         aligned term.
#         :return: Boolean value whether or not it matches the criteria
#         """
#         _MAX_NUM_TOKENS = max_tokens
#         _stopwords = nltk.corpus.stopwords.words('english')
#         word_frequencies = {}
#         snt_scores = {}
#         for word in nltk.word_tokenize(self._snts):
#             if word not in _stopwords:
#                 if word not in word_frequencies.keys():
#                     word_frequencies[word] = 1
#                 else:
#                     word_frequencies[word] += 1
#
#         max_wfreq = max(word_frequencies.values())
#         for word in word_frequencies.keys():
#             word_frequencies[word] = word_frequencies[word] / max_wfreq
#
#         for snt in self._snts:
#             for word in nltk.word_tokenize(snt.lower()):
#                 if len(snt.split(' ')) < _MAX_NUM_TOKENS:
#                     if snt not in snt_scores.keys():
#                         snt_scores[snt] = word_frequencies[word]
#                         snt_scores[snt] = word_frequencies[word]
#
#         summary_descr = max(snt_scores, key=snt_scores.get)
#         _worked = False
#         for sub in self._aligned_subs:
#             if sub in summary_descr:
#                 _worked = True
#                 self._gen_descr.append(
#                     self._paint_alignment(summary_descr, self._aligned_subs)
#                 )
#
#         return _worked
#
#     def _n_match_gen(self):
#         self._snts_to_amr()
#         _alignments = []
#         _snt_chosen = []
#         _worked = False
#         if self._amr_list:
#             for amr in self._amr_list:
#                 for pair in combinations(self._aligned_subs, r=2):
#                     if amr.is_node(pair[0].term) and amr.is_node(pair[1].term):
#                         _worked = True
#                         if amr.snt not in self._gen_descr:
#                             _snt_chosen.append(amr.snt)
#                             _alignments += [pair[0], pair[1]]
#
#         _snt_chosen = list(set(_snt_chosen))
#         for snt in _snt_chosen:
#             painted_snt = self._paint_alignment(snt, _alignments)
#             self._gen_descr.append(painted_snt)
#
#         return _worked
#
#     def _merge_amr(self):
#         # source sentence selection
#         # TODO:
#
#         # content planning
#         # TODO:
#
#         # surface realization
#         # TODO:
#
#         pass
#
#     def _apply_criteria(self, crit_type=None):
#         """
#         Criteria for confirming description
#         :arg crit_type: which criteria
#         :return: Boolean value whether or not it matches the criteria
#         """
#         _worked = False
#         if crit_type is not None:
#             # match 2 AMR entities
#             if crit_type.upper() == "2-MATCH":
#                 _worked = self._two_match_gen()
#             elif crit_type.upper() == "SUMMARIZING":
#                 _worked = self._summarizing_gen()
#             elif crit_type.upper() == "N-MATCH":
#                 _worked = self._n_match_gen()
#
#         return _worked
#
#     def _snts_to_amr(self):
#         """
#         Transform natural language sentences to an AMR graph
#         :return: an AMR object
#         """
#         if self._snts is not None and len(self._snts) >= 1:
#             self._amr_list = wrapper.parse_to_amr_list(snts=self._snts)
#             self._amr_list = list(set(self._amr_list))
#
#     def generate_descriptions(self, type="2-MATCH"):
#         if self._apply_criteria(crit_type=type.replace(" ", "")):
#             print("[IDG] Success!")
#             return True
#         else:
#             print("[IDG] No img description generated :(")
#             return False
#
#     def get_gen_descr(self):
#         return self._gen_descr
