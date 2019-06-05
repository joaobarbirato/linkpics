"""
    Register every alignment occurred, as well as it's elements
    @author: João Gabriel Melo Barbirato
"""
from sqlalchemy.orm.collections import InstrumentedList

from app.eval_module.models import query_by_id, PredAlignment
from app.src.VC.boundingBox import BoundingBox


def _add(list_object, element):
    if list_object is None:
        list_object = [element]
    elif isinstance(list_object, list):
        list_object.append(element)
    else:
        list_object = [list_object, element]
    return list_object


def _add_relation(model, object):
    if object is not None:
        if isinstance(object, list):
            model.extend(object)
        else:
            model.append(object)

    return model


def _add_session(object):
    if object is not None:
        if isinstance(object, list):
            db.session.add_all(object)
        else:
            db.session.add(object)


from app import db


def add_db_alignments_from_list(list_alignments):
    db.session.add_all(list_alignments)


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())


class MWE(Base):
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


class Synonym(Base):
    __tablename__ = 'synonym'
    syn = db.Column(db.String, nullable=False, default='')
    approval = db.Column(db.Boolean, nullable=True)
    aligment_id = db.Column(db.Integer, db.ForeignKey('alignment.id'), nullable=False)

    def __init__(self, syn):
        self.syn = syn

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
        if isinstance(other, Synonym):
            return self.syn == other.syn
        elif isinstance(other, str):
            return self.syn == other

    def __repr__(self):
        return self.sym

    def __str__(self):
        return self.syn


class Color(Base):
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


class Alignment(Base):
    """
    main class
    """
    __tablename__ = 'alignment'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('eval_align.id'), nullable=False)
    term = db.Column(db.String, nullable=True)
    occurrence = db.Column(db.Integer, nullable=False, default=1)
    colors_model = db.relationship('Color', single_parent=True, backref='alignment', cascade='all, delete-orphan',
                                   lazy=True, uselist=False)
    mwes_model = db.relationship('MWE', single_parent=True, backref='alignment', cascade='all, delete-orphan',
                                 lazy=True)
    syns_model = db.relationship('Synonym', single_parent=True, backref='alignment', cascade='all, delete-orphan',
                                 lazy=True)

    is_ne = db.Column(db.Boolean, nullable=True)

    def __init__(self, bounding_box, term, mwe=None, syns=None, is_ne=False, html_color=None, img_color=None):
        self.term = term
        self.is_ne = is_ne

        # 1:n alignment
        self.list_bounding_box = bounding_box
        self.occurrence = 1 if isinstance(self.list_bounding_box, BoundingBox) else len(bounding_box)

        # multi-word expressions
        self.list_mwe = mwe
        self.has_mwe = self.list_mwe is not None

        # n:1 alignment
        self.list_syns = syns
        self.has_syns = self.list_syns is not None

        self.color = html_color
        self.html_color = html_color
        self.img_color = img_color

    def add_occurrence(self, bounding_box=None):
        """
        Add occurrence to an alignment
        :param bounding_box: bounding box to a new occurrence
        :return: a list of all bounding boxes connected to self.term
        """
        if bounding_box is not None:
            self.list_bounding_box = _add(self.list_bounding_box, bounding_box)
            self.occurrence = len(self.list_bounding_box)
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

    def get_color(self):
        return self.color

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

    def get_len_mwes_model(self):
        """
        Inform how many multi-word expressions are associated with an alignment
        :return: length of mwes_model relationship array
        """
        return len(self.mwes_model) if self.mwes_model else 0

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


class AlignmentGroup:
    def __init__(self, name=None):
        self.name = name
        self.list_alignments = []

    def _query_term(self, x):
        return [algn for algn in self.list_alignments if
                algn.term == x or algn.is_syn(x) or (algn.is_ne and x in algn.term) or
                (not algn.is_ne and x.replace(" ", "") == algn.term) or
                (algn.is_ne and algn.term in x)]

    def add_alignments(self, alignment=None):
        if alignment is not None:
            if isinstance(alignment, Alignment):
                # if not self._query_term(alignment.term):
                self.list_alignments.append(alignment)

            elif isinstance(alignment, list):
                for a in alignment:
                    # if not self._query_term(a.term):
                    self.list_alignments.append(a)

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


def init():
    global ALIGNMENTS, GROUPS
    ALIGNMENTS = AlignmentGroup()
    GROUPS = {}
