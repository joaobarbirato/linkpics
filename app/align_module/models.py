"""
    Register every alignment occurred, as well as it's elements
    @author: João Gabriel Melo Barbirato
"""
from sqlalchemy.orm.collections import InstrumentedList

from app.align_module import _treat_raw_text
from app.align_module.base_model import Token, MWE, Synonym, Color, Sentence
from app.align_module.coref_models import MentionModel, CoreferenceModel
from app.src.PLN.coreference import Coreference
from app.src.VC.boundingBox import BoundingBox
from app import (db)
from app.model_utils import BaseModel, _add, _add_relation, _add_session
from app.src.util.utils import word_to_wordpoint, mwe_with_separators

occur = db.Table('occur',
                 db.Column('sentence_id', db.Integer, db.ForeignKey('sentence.id'), primary_key=True),
                 db.Column('alignment_id', db.Integer, db.ForeignKey('alignment.id'), primary_key=True)
                 )

from app.desc_module.models import Description


class Alignment(BaseModel):
    """
    main class
    """
    __tablename__ = 'alignment'

    model_id = db.Column(db.Integer, db.ForeignKey('eval_align.id'))
    term = db.Column(db.String, nullable=True)
    occurrence_times = db.Column(db.Integer, nullable=False, default=1)

    colors_model = db.relationship('Color', single_parent=True, backref='alignment', cascade='all, delete-orphan',
                                   lazy=True, uselist=False)
    mwes_model = db.relationship('MWE', single_parent=True, backref='alignment', cascade='all, delete-orphan',
                                 lazy=True)
    syns_model = db.relationship('Synonym', single_parent=True, backref='alignment', cascade='all, delete-orphan',
                                 lazy=True)
    belongs_sentence = db.relationship('Sentence', secondary=occur, lazy='subquery',
                                       backref=db.backref('has_alignment', lazy=True))

    group_id = db.Column(db.Integer, db.ForeignKey('alignment_group.id'))

    is_ne = db.Column(db.Boolean, nullable=True)

    description = db.relationship('Description', single_parent=True, uselist=False, backref='alignment', lazy=True)

    def __init__(self, bounding_box, term, mwe=None, syns=None, is_ne=False, html_color=None, img_color=None):
        self.term = term
        self.is_ne = is_ne

        # 1:n alignment
        self.list_bounding_box = bounding_box
        self.occurrence_times = 1 if isinstance(self.list_bounding_box, BoundingBox) else len(bounding_box)

        # multi-word expressions
        self.list_mwe = mwe
        self.has_mwe = self.list_mwe is not None

        # n:1 alignment
        self.list_syns = syns
        self.has_syns = self.list_syns is not None

        self.color = html_color
        self.html_color = html_color
        self.img_color = img_color

    def add_occurrence_times(self, bounding_box=None):
        """
        Add occurrence_times to an alignment
        :param bounding_box: bounding box to a new occurrence_times
        :return: a list of all bounding boxes connected to self.term
        """
        if bounding_box is not None:
            self.list_bounding_box = _add(self.list_bounding_box, bounding_box)
            self.occurrence_times = len(self.list_bounding_box)
            return self.list_bounding_box

    def add_mwe(self, mwe=None):
        """
        Add mwe to an alignment
        :param mwe: multi-word expression containing self.term
        :return: a list of all multi-word expressions
        """
        if mwe is not None:
            if self.list_mwe is None or mwe not in self.list_mwe:
                self.list_mwe = _add(self.list_mwe, MWE(mwe))
                self.has_mwe = self.list_mwe is not None

            return self.list_mwe

    def add_mwe_model(self, mwe=None):
        """

        :param mwe:
        :return:
        """
        if isinstance(mwe, InstrumentedList):
            self.mwes_model = _add_relation(self.mwes_model, mwe)
            return self.mwes_model

    def add_syn(self, syn=None):
        """
        Add syn to an alignment
        :param syn: synonym of self.term
        :return: a list of all synonyms
        """
        if syn is not None and syn:
            if self.list_syns is None or syn not in self.list_syns:
                self.list_syns = _add(self.list_syns, Synonym(syn))
                self.has_syns = self.list_syns is not None
            return self.list_syns

    def add_color(self, color=None):
        """
        Add a color to alignment
        :param color: color in RGB pattern
        :return: list of colors
        """
        if color is not None:
            if isinstance(color, tuple) and (self.color is None or color != self.color):
                self.color = Color(color[0], color[1], color[2])

                return self.color

    def add_sentence(self, sentence=None):
        """

        :type sentence: app.align_module.base_model.Sentence, list
        :param sentence:
        :return:
        """
        if sentence is not None and sentence:
            if self.belongs_sentence is None or \
                    ((isinstance(sentence, list) and all(s not in self.belongs_sentence for s in sentence)) or
                     (isinstance(sentence, Sentence) and sentence not in self.belongs_sentence)):
                self.belongs_sentence = _add_relation(self.belongs_sentence, sentence)

        return self.belongs_sentence

    def add_description(self, description):
        """

        :param alignment:
        :return:
        """
        self.description = description
        return self.description

    def get_term(self):
        return self.term

    def get_color(self):
        return self.color

    def get_syns(self):
        return self.syns_model

    def get_mwes(self):
        return self.mwes_model

    def is_syn(self, syn=None):
        """
        Inform if a given term is synonym of self.term
        :param syn: given term
        :return: true if it is, false if it isn't
        """
        return [_syn for _syn in self.list_syns if _syn == syn] != [] if self.list_syns is not None else False

    def get_is_ne(self):
        """
        Inform if an alignment is a named entity
        :return: true if it is, false if it isn't
        """
        return self.is_ne

    def get_has_syns_model(self):
        """
        Inform if an alignment is associated with synonyms found at the text
        :return: true if it is, false if it isn't
        """
        return bool(self.syns_model)

    def get_len_syns_model(self):
        """
        Inform how many synonyms are associated with an alignment
        :return: length of syns_model relationship array
        """
        return len(self.syns_model) if self.syns_model else 0

    def get_has_mwes_model(self):
        """
        Inform if an alignment is associated with multi-word expressions found at the text
        :return: true if it is, false if it isn't
        """
        return bool(self.mwes_model)

    def sentences(self):
        return self.belongs_sentence

    def get_len_mwes_model(self):
        """
        Inform how many multi-word expressions are associated with an alignment
        :return: length of mwes_model relationship array
        """
        return len(self.mwes_model) if self.mwes_model else 0

    def get_description(self):
        return self.description

    def has_color(self):
        """
        Inform if an alignment has a color
        :return: boolean True if it has, False otherwise
        """
        return self.color is not None

    def __str__(self):
        return self.term

    def __repr__(self):
        return self.term

    def add_to_db(self):
        self.colors_model = self.color
        self.syns_model = _add_relation(self.syns_model, self.list_syns)
        self.mwes_model = _add_relation(self.mwes_model, self.list_mwe)

        _add_session(self.color)
        _add_session(self.list_syns)
        _add_session(self.list_mwe)
        _add_session(self)

    def save(self):
        db.session.add(self)
        db.session.commit()


class AlignmentGroup(BaseModel):
    __tablename__ = 'alignment_group'

    list_alignments = db.relationship('Alignment', single_parent=True, backref='alignment_group',
                                      cascade='all, delete-orphan', lazy=True)

    def __init__(self, name=None):
        self.name = name

    def _query_term(self, x):
        return [algn for algn in self.list_alignments if
                algn.term == x or algn.is_syn(x) or (algn.is_ne and x in algn.term) or
                (not algn.is_ne and x.replace(" ", "") == algn.term) or
                (algn.is_ne and algn.term in x)]

    def add_alignments(self, alignment=None):
        """
        Add alignment to a group
        :param alignment: alignment object
        :type alignment: Alignment
        :return: list of all alignments
        """
        if alignment is not None and alignment:
            if self.list_alignments is None or alignment not in self.list_alignments:
                self.list_alignments = _add_relation(self.list_alignments, alignment)

        return self.list_alignments

    def get_alignment(self, term=None, index=0):
        return self._query_term(term)[index]

    def has_alignment(self, term=None):
        if term is not None:
            return self._query_term(term) != []

    def get_list_terms(self):
        return [algn.term for algn in self.list_alignments]

    def get_all_alignments(self):
        return self.list_alignments

    def __str__(self):
        return self.name

    def __exit__(self, exc_type, exc_value, traceback):
        db.session.expunge_all()
        pass

    def add_db_all_alignments(self):
        db.session.add_all(self.list_alignments)
        db.session.add(self)


def get_all_news():
    return News.query.all()


class News(BaseModel):
    __tablename__ = 'news'
    img_path = db.Column(db.String, nullable=False, default='')
    sentences = db.relationship('Sentence', single_parent=True, backref='news',
                                cascade='all, delete-orphan', lazy=True)
    coreferences = db.relationship('CoreferenceModel', single_parent=True, backref='news', cascade='all, delete-orphan',
                                   lazy=True)
    link = db.Column(db.String, nullable=False, default='')

    def __init__(self, path=None, link=''):
        self.img_path = path
        self.link = link

    def set_path(self, path):
        """

        :type path: str
        :param path:
        :return:
        """
        self.img_path = path

    def set_link(self, link):
        """

        :param link:
        :return:
        """
        self.link = link

    def add_sentence(self, sentence):
        """

        :type sentence: app.align_module.base_model.Sentence
        :param sentence:
        :return:
        """
        if sentence is not None and sentence:
            if self.sentences is None or sentence not in self.sentences:
                self.sentences = _add_relation(self.sentences, sentence)
        return self.sentences

    def add_coreference(self, coref):
        """

        :param coref:
        :return:
        """
        if coref is not None and coref:
            if self.coreferences is None or coref not in self.coreferences:
                self.coreferences = _add_relation(self.coreferences, coref)

    def add_from_zip_list(self, tkn_snt_list):
        """

        :param tkn_snt_list:
        :return:
        """
        for index, (snt, tknized) in enumerate(tkn_snt_list):
            if index == 0:
                label = 'title'
            elif index == 1:
                label = 'subtitle'
            else:
                label = 'text'
            snt_model = Sentence(text=snt, label=label)

            for tkn in tknized:
                tkn_model = Token(tkn.marshal())
                snt_model.add_tokenized(tkn_model)
                # _add_session(tkn_model)

            self.sentences = _add_relation(self.sentences, snt_model)
            # _add_session(snt_model)

    def add_from_coref_objects(self, coref_object):
        """

        :param coref_object: list
        :return:
        """
        coref: Coreference
        for coref in coref_object:
            _coref_model = CoreferenceModel()
            _mention_list = []
            for mention in coref.get_mentions():
                _sentence = self.get_sentence_index(index=int(mention.sentence) - 1)
                _tokens = _sentence.get_tokens(start=mention.start, end=mention.end )
                _m = MentionModel(
                    start=mention.start,
                    head=mention.head,
                    end=mention.end,
                    tokens=InstrumentedList(_tokens)
                )
                _mention_list.append(_m)

            _coref_model.add_mention(_mention_list)
            self.coreferences = _add_relation(self.coreferences, _coref_model)

    def alignments(self):
        return InstrumentedList(set(sum([s.get_alignments() for s in self.sentences], [])))

    def get_coreferences(self, term=None):
        if term is None:
            return self.coreferences
        else:
            if isinstance(term, str):
                return InstrumentedList(coref for coref in self.coreferences
                                        if coref.has_term(term))
            elif isinstance(term, list or InstrumentedList):
                if isinstance(term[0], str):
                    return InstrumentedList(coref for coref in self.coreferences
                                            if any(coref.has_term(t) for t in term))
                elif isinstance(term[0], list or InstrumentedList):
                    return InstrumentedList(coref for coref in self.coreferences
                                            if any(all(coref.has_term(compound) for compound in t) for t in term))

    def get_sentence_index(self, index=0):
        if isinstance(index, int):
            return self.sentences[index]
        elif isinstance(index, list):
            return [self.sentences[i] for i in index]

    def get_full_text(self):
        return f'{self.sentences[0]}\n{self.sentences[1]}\n{"".join(str(s) for s in self.sentences[2:])}'

    def _highlight_alignments(self, text):
        """

        :type text: str
        """
        new_text = text
        alignment: Alignment
        for alignment in self.alignments():
            pre_tag = f'<b style="color:rgb({str(alignment.colors_model)});">'
            pos_tag = f'</b>'
            if alignment.get_mwes():
                for mwe in alignment.get_mwes():
                    for word in mwe_with_separators(mwe.mwe):
                        new_text = new_text.replace(word, f'{pre_tag}{word}{pos_tag}')
            if alignment.get_syns():
                for syn in alignment.get_syns():
                    for word in word_to_wordpoint(syn.syn):
                        new_text = new_text.replace(word, f'{pre_tag}{word}{pos_tag}')

            for word in word_to_wordpoint(alignment.get_term()):
                new_text = new_text.replace(word, f'{pre_tag}{word}{pos_tag}')

        return new_text

    def get_title(self, highlight_alignments=False):
        if not highlight_alignments:
            return f'{self.sentences[0]}'
        else:
            return self._highlight_alignments(f'{self.sentences[0]}')

    def get_subtitle(self, highlight_alignments=False):
        if not highlight_alignments:
            return f'{self.sentences[1]}'
        else:
            return self._highlight_alignments(f'{self.sentences[1]}')

    def get_text(self, highlight_alignments=False):
        if not highlight_alignments:
            return _treat_raw_text(f'{"".join(str(s) for s in self.sentences[2:])}')
        else:
            return self._highlight_alignments(_treat_raw_text(f'{"".join(str(s) for s in self.sentences[2:])}'))

    def get_link(self):
        return self.link

    def get_sentences(self, return_type="model", position=None):
        if return_type == "str":
            if position is not None:
                if isinstance(position, int) and position >= 0:
                    return str(self.sentences[position])
                elif isinstance(position, list):
                    return [str(s) for i, s in enumerate(self.sentences) if i in position]
            else:
                return [str(s) for s in self.sentences]
        elif return_type == "model":
            if position is not None:
                if isinstance(position, int) and position >= 0:
                    return self.sentences[position]
                elif isinstance(position, list):
                    return [s for i, s in enumerate(self.sentences) if i in position]
            else:
                return self.sentences

        return []

    def as_dict(self):
        return {"img_path": self.img_path, "sentences": {s.as_dict() for s in self.sentences}}

    def save(self):
        # [sentence.save() for sentence in self.sentences]
        # [coref.save() for coref in self.coreferences]
        _add_session(self)


def init():
    global ALIGNMENTS, GROUPS
    ALIGNMENTS = AlignmentGroup()
    GROUPS = {}
