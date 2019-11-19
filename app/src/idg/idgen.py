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
            generated_text_list = []
            for alignment, generated_amr, _, _ in descr_to_generate:
                amr_to_generate_text.append(generated_amr)

                generated_text_list = penman_to_text(amr_list=amr_to_generate_text)
            for ((alignment, generated_amr, main_ancestral, adjacent_ancestral), _generated_text) \
                    in zip(descr_to_generate, generated_text_list):

                _generated_text = self.pre_process_text(text=_generated_text)
                description = create_description(text=_generated_text, method=method)
                description.add_amr(generated_amr)
                description.save()
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

    def pre_process_text(self, text):
        """

        :type text: str
        """
        text = text.replace(" .", "")
        if text[-1] == '':
            text = text[:-1]
        text = text.replace(" :", "")
        text = self._remove_repeated_words(text)
        return text

    def _remove_repeated_words(self, text):
        from nltk.tokenize import wordpunct_tokenize
        tokenized = wordpunct_tokenize(text=text)
        new_tokenized = []
        for i, token in enumerate(tokenized):
            is_repeated = False
            if i > 0 and tokenized[i-1] == token:
                is_repeated = True
            if not is_repeated:
                new_tokenized.append(token)

        from nltk.tokenize.treebank import TreebankWordDetokenizer
        new_text = TreebankWordDetokenizer().detokenize(new_tokenized)
        return new_text
