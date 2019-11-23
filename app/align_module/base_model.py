from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import InstrumentedList

from app import db
from app.align_module import _treat_raw_text
from app.eval_module.models import query_by_id, PredAlignment
from app.model_utils import BaseModel, _add_session, _add_relation


def create_token(**kwargs):
    return Token(**kwargs)


has_syn_snt = db.Table('has_syn',
                       db.Column('sentence_id', db.Integer, db.ForeignKey('sentence.id'), primary_key=True),
                       db.Column('synonym_id', db.Integer, db.ForeignKey('synonym.id'), primary_key=True)
                       )


class Token(BaseModel):
    word = db.Column(db.String)
    lemma = db.Column(db.String)
    pos = db.Column(db.String)
    ner = db.Column(db.Boolean, nullable=False, default=False)

    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'), nullable=False)
    mention_id = db.Column(db.Integer, db.ForeignKey('mention_model.id'), nullable=True)

    def __init__(self, dictionary):
        self.word = dictionary['word']
        self.lemma = dictionary['lemma']
        self.pos = dictionary['pos']
        self.ner = dictionary['ner'] != '0'

    def __repr__(self):
        return self.word

    def __str__(self):
        return self.word

    def __eq__(self, other):
        if isinstance(other, str):
            return self.lemma == other or self.word == other
        elif isinstance(other, Token):
            return self.lemma == self.lemma

    def __hash__(self):
        return hash(self.word)

    def get_sentence(self):
        return self.sentence

    def save(self):
        _add_session(self)


class MWE(BaseModel):
    __tablename__ = 'mwe'

    mwe = db.Column(db.String, nullable=False, default='')
    approval = db.Column(db.Boolean, nullable=True)
    aligment_id = db.Column(db.Integer, db.ForeignKey('alignment.id'), nullable=False)

    def __init__(self, mwe):
        self.mwe = mwe

    def get_parent(self):
        return query_by_id(PredAlignment, self.aligment_id)

    def set_approval(self, appr):
        if isinstance(appr, bool):
            self.approval = appr
            return True
        return False

    def add_self(self):
        _add_session(self)

    def __eq__(self, other):
        if isinstance(other, MWE):
            return self.mwe == other.mwe
        elif isinstance(other, str):
            return self.mwe == other

    def __repr__(self):
        return self.mwe

    def __str__(self):
        return self.mwe


class Synonym(BaseModel):
    __tablename__ = 'synonym'

    syn = db.Column(db.String, nullable=False, default='')
    approval = db.Column(db.Boolean, nullable=True)
    aligment_id = db.Column(db.Integer, db.ForeignKey('alignment.id'), nullable=False)

    belongs_sentence = db.relationship('Sentence', secondary=has_syn_snt, lazy='subquery',
                                       backref=db.backref('has_synonym', lazy=True))

    def __init__(self, syn):
        self.syn = syn

    def get_parent(self):
        return query_by_id(PredAlignment, self.aligment_id)

    def set_approval(self, appr):
        if isinstance(appr, bool):
            self.approval = appr
            return True
        return False

    def add_sentence(self, sentence=None):
        return _add_relation(self.belongs_sentence, sentence)

    def sentences(self):
        return self.belongs_sentence

    def add_self(self):
        _add_session(self)

    def __eq__(self, other):
        if isinstance(other, Synonym):
            return self.syn == other.syn
        elif isinstance(other, str):
            return self.syn == other

    def __repr__(self):
        return self.syn

    def __str__(self):
        return self.syn


class Color(BaseModel):
    __tablename__ = 'color'

    red = db.Column(db.Integer, nullable=False, default=0)
    green = db.Column(db.Integer, nullable=False, default=0)
    blue = db.Column(db.Integer, nullable=False, default=0)
    aligment_id = db.Column(db.Integer, db.ForeignKey('alignment.id'), nullable=False)

    def __init__(self, r, g, b):
        self.red = r
        self.green = g
        self.blue = b

    def __eq__(self, other):
        if isinstance(other, Color):
            return self.red == other.red and self.green == other.green and self.blue == other.blue
        elif isinstance(other, tuple):
            return self.red == other[0] and self.green == other[1] and self.blue == other[2]

    def get_html_color(self):
        return self.red, self.green, self.blue

    def get_bb_color(self):
        return self.blue, self.green, self.red

    def __repr__(self):
        return "<Color ", self.get_html_color(), ">"

    def __str__(self):
        return "%d, %d, %d" % (self.get_html_color()[0], self.get_html_color()[1], self.get_html_color()[2])


def create_sentence(**kwargs):
    return Sentence(**kwargs)


class Sentence(BaseModel):
    __tablename__ = 'sentence'
    label = db.Column(db.String(16), nullable=False, default='text')
    content = db.Column(db.String, nullable=False, default='')
    tokenized = db.relationship('Token', single_parent=True, backref='sentence',
                                cascade='all, delete-orphan', lazy=True)
    amr = db.relationship('AMRModel', backref=backref('sentence', enable_typechecks=False, lazy=True),
                          cascade='all, delete-orphan', lazy=True, uselist=False)

    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=True)

    __mapper_args = {
        'polymorphic_on': 'sentence_type',
        'polymorphic_identity': 'sentence'
    }

    def __init__(self, **kwargs):
        if kwargs:
            if len(kwargs) == 2 and ('text' and 'label') in kwargs:
                self.content = kwargs['text']
                self.label = kwargs['label']
            elif len(kwargs) == 1 and 'copy' in kwargs:
                kwargs['copy']: Sentence
                self.content = kwargs['copy'].content
                self.label = kwargs['copy'].label
                self.tokenized = InstrumentedList([
                    create_token(dictionary={'word': token.word, 'lemma': token.lemma, 'ner': token.ner, 'pos': token.pos})
                    for token in kwargs['copy'].tokenized
                ])

    def __repr__(self):
        return _treat_raw_text(self.content)

    def __str__(self):
        return _treat_raw_text(self.content)

    def __hash__(self):
        return hash(_treat_raw_text(self.content))

    def get_tokens(self, start, end):
        return self.tokenized[start-1:end-1]

    def add_tokenized(self, token):
        """

        :type token: app.align_module.base_model.Token
        :param token:
        :return:
        """
        if token is not None and token:
            if self.tokenized is not None or token not in self.tokenized:
                self.tokenized = _add_relation(self.tokenized, token)
        return self.tokenized

    def add_amr(self, amr):
        """

        :type amr: AMRModel
        :param amr:
        :return:
        """
        if amr is not None and amr:
            if self.amr is None:
                self.amr = amr
        return self.amr

    def get_amr(self):
        return self.amr

    def get_synonyms(self):
        return self.has_synonym

    def get_alignments(self):
        return self.has_alignment

    def as_dict(self):
        return {"label": self.label, "content": self.content, "news_id": self.news_id, "amr": self.amr}

    def get_words_from_lemma(self, lemma=None):
        if lemma is not None:
            return [token.word for token in self.tokenized if token.lemma == lemma]
        return []

    def save(self):
        [token.save() for token in self.tokenized]


def sntsmodel_to_amrmodel(snts):
    return InstrumentedList(snt.get_amr() for snt in snts)
