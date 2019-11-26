"""
    Image Description Generator
    @author: João Gabriel Melo Barbirato
"""
from itertools import product

from app.align_module.coref_models import CoreferenceModel, MentionModel
from app.amr_module.models import AMRModel, biggest_amr, create_amrmodel
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

        self._source_sentences = None
        self.src_focus = []

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

    def generate(self, method='baseline5', select=1):
        """

        :return:
        """
        try:
            all_alignments = self.news_object.alignments()

            descr_to_generate = []

            alignment: Alignment
            for alignment in all_alignments:
                self._source_sentences = self.sentence_selection(alignment=alignment, select=select)
                self._current_alignment = alignment
                try:
                    response = self._generate_amr(method=method)
                    if response is not None:
                        generated_amr, main_ancestral, adjacent_ancestral, focus_list = response
                        descr_to_generate.append((alignment, generated_amr, main_ancestral, adjacent_ancestral,
                                                  focus_list))
                except Exception as exc:
                    PrintException()
                    print(f'[{__file__}] Error while generating AMR from {alignment}: {str(exc)}')

            amr_to_generate_text = []
            generated_text_list = []
            for alignment, generated_amr, _, _, _ in descr_to_generate:
                amr_to_generate_text.append(generated_amr)

                generated_text_list = penman_to_text(amr_list=amr_to_generate_text)
            for ((alignment, generated_amr, main_ancestral, adjacent_ancestral, focus_list), _generated_text) \
                    in zip(descr_to_generate, generated_text_list):

                _generated_text = self.post_process(text=_generated_text, amr=generated_amr)
                description = create_description(text=_generated_text, method=method)
                description.method = f'{method}|{str(select)}'
                description.add_amr(generated_amr)
                description.set_used_focus(focus_list)
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
            try:
                amr_list = sntsmodel_to_amrmodel([source for source, focus in self.src_focus])
                information = []
                amr: AMRModel
                print(self.src_focus)
                for focus_term, amr in zip([focus for source, focus in self.src_focus], amr_list):
                    is_name = amr.is_name(focus_term)
                    if not is_name:
                        focus_triple = amr.get_triple(relation='instance', target=focus_term)
                    else:
                        focus_triple = is_name
                    if focus_triple is not None and focus_triple:
                        focus_subgraph = amr.get_subgraph(top=focus_triple)
                        focus_parent = amr.get_parents(focus_triple)
                        information.append(
                            {
                                "triple": focus_triple,
                                "subgraph": create_amrmodel(copy=focus_subgraph),
                                "parent": focus_parent,
                                "amr": amr
                            }
                        )

                if information:
                    base_info, information = self._choose_biggest(information)

                    # consider parents
                    if method == 'baseline4':
                        base_info = self._add_parent_to_base(info=base_info, base=base_info)

                    appended_amr_list = []
                    before = base_info["subgraph"].get_penman(return_type='str', indent=True)
                    if len(information) > 1:
                        for info in information:
                            base_info["subgraph"].add(other=info["subgraph"],
                                                      tuple_ref=(base_info["triple"].source, info["triple"].source))

                            # consider parents
                            if method == 'baseline4':
                                base_info = self._add_parent_to_base(info=info, base=base_info)

                            if before != base_info["subgraph"].get_penman(return_type='str', indent=True):
                                appended_amr_list.append(info)

                    return base_info["subgraph"], base_info["amr"], [info["amr"] for info in appended_amr_list], \
                           [str(info["triple"]) for info in appended_amr_list]
            except Exception as exc:
                PrintException()
                print(f'Error on {method}: {str(exc)}')
        except Exception as exc:
            PrintException()
            print(f'[{__file__}] Error while generating AMR: {str(exc)}')

    def _choose_biggest(self, info_list):
        found = False
        copy_info_list = info_list
        base_info = None
        from nltk.stem import WordNetLemmatizer
        lemmatizer = WordNetLemmatizer()
        while not found and copy_info_list:
            biggest_subgraph = biggest_amr([info["subgraph"] for info in copy_info_list])
            base_info = [info for info in copy_info_list if info["subgraph"] == biggest_subgraph][0]
            if lemmatizer.lemmatize(self._current_alignment.get_term()).upper() == base_info["triple"].target.upper():
                found = True
            copy_info_list.remove(base_info)
        return base_info, copy_info_list

    @staticmethod
    def _add_parent_to_base(info, base):
        if info["parent"]:
            info["parent"][1].invert()
            base["subgraph"].add(
                other=create_amrmodel(triples=info["parent"], top=info["parent"][2].source),
                tuple_ref=(base["triple"].source, info["parent"][2].source))
        return base

    def sentence_selection(self, select=0, alignment=None):
        from nltk.stem import WordNetLemmatizer
        lemmatizer = WordNetLemmatizer()
        # alignments only
        if select == 0:
            self._source_sentences = alignment.sentences()
            from itertools import cycle
            self.src_focus = [(sentence, focus) for sentence, focus in zip(self._source_sentences, cycle([lemmatizer.lemmatize(alignment.get_term())]))]
            self.src_focus.sort()
            return self.src_focus

        # alignments and it's corefs
        elif select == 1:
            src_focus_0 = self.sentence_selection(select=0, alignment=alignment)
            src_focus_1 = []
            all_corefs = self.news_object.get_coreferences()
            coref: CoreferenceModel
            for coref in all_corefs:
                mention: MentionModel
                for mention in coref.get_mentions():
                    tokens = mention.has_term(alignment.get_term())
                    if tokens:
                        src_focus_1 += [(token.get_sentence(), token.lemma) for token in mention.get_tokens() if 'NN' in token.pos or 'PP' in token.pos]

            self.src_focus = list(set(src_focus_1 + src_focus_0))
            self.src_focus.sort()
            return self.src_focus

        # alignments, corefs and some TODO WordNet relation
        elif select == 2:
            if alignment.has_syns:
                src_focus_1 = self.sentence_selection(select=1, alignment=alignment)
                synonyms = alignment.get_syns()
                src_focus_2 = []
                for synonym in synonyms:
                    src_focus_2 += [(src, focus) for src, focus in product(synonym.sentences(), [lemmatizer.lemmatize(synonym)])]
                self.src_focus = list(set(src_focus_2 + src_focus_1))
                self.src_focus.sort()
                return self.src_focus
            else:
                return self.sentence_selection(select=1, alignment=alignment)

        else:
            return self.sentence_selection(0)

    def post_process_text(self, text):
        """

        :type text: str
        """
        new_text = text.replace(" .", "")
        if new_text[-1] == ' ':
            new_text = new_text[:-1]

        if new_text[0] == ' ':
            new_text = new_text[1:]

        new_text = new_text.replace(" :", "")
        new_text = self._remove_repeated_words(new_text)
        return new_text

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

    def generate_from_mod_sequence(self, src, amr):
        p = list(set(amr.span(amr.get_instance(amr.top))) - set(amr.get_triples(relation='instance')))
        if p:
            return ' '.join([self.generate_from_mod_sequence(src=way.target, amr=amr) for way in p if way.source == src]) + \
                   ' ' + amr.get_instance(src=src).target
        else:
            return amr.get_instance(src=src).target

    def post_process(self, text, amr):
        """

        :type text: str
        :type amr: AMRModel
        """
        new_text = self.post_process_text(text=text)
        from nltk.tokenize import wordpunct_tokenize
        tokenized_text = wordpunct_tokenize(new_text)
        from nltk.stem import WordNetLemmatizer
        lemmatizer = WordNetLemmatizer()
        if (amr.get_size() == 1 and len(amr.get_triples()) == 1) and \
                amr.get_triples()[0].target not in [lemmatizer.lemmatize(token) for token in tokenized_text]:
            new_text = amr.get_triples()[0].target
        elif (amr.get_size() == 1 and len(amr.get_triples()) > 1) and amr.get_triples()[0].target == 'name':
            instance = amr.get_triples(relation='instance')[0]
            names = amr.get_triples(src=instance.source)
            names.remove(instance)
            new_text = " ".join([t.target for t in names])

        if all(triple.relation == 'mod' for triple in list(set(amr.span(amr.get_instance(amr.top))) - set(amr.get_triples(relation='instance')))):
            new_text = self.generate_from_mod_sequence(src=amr.top, amr=amr)
        return new_text
