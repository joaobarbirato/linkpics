# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
import os

from app import db

from app.model_utils import Base
from config import STATIC_REL


def get_all_batch():
    """
    Get all batch objects
    :return: db query of all batch objects
    """
    return Batch.query.all()


def get_all_em():
    """
    Get all EvalModel objects
    :return: db query of all batch objects
    """
    return EvalModel.query.all()


def exists_aem(aem):
    return db.session.query(db.exists().where(PredAlignment.id == aem.id)).scalar()


def exists_em(em):
    return db.session.query(db.exists().where(EvalModel.id == em.id)).scalar()


class PredAlignment(Base):
    __tablename__ = 'eval_align'
    label = db.Column(db.String(255), nullable=False, default='')
    approval = db.Column(db.Boolean, nullable=True)
    alignment = db.relationship('Alignment', backref='eval_align', cascade="all, delete-orphan", uselist=False, lazy=True)

    mwe_contrib = db.Column(db.String(4), nullable=True)
    syn_contrib = db.Column(db.String(4), nullable=True)

    eval_id = db.Column(db.Integer, db.ForeignKey('eval.id'), nullable=False)
    comments = db.Column(db.String, nullable=True)

    def __init__(self, label, alignment):
        self.label = label
        self.alignment = alignment

    def __repr__(self):
        return '<Align Model %r>' % self.label

    def add_comment(self, comment):
        self.comments = comment

    def was_eval(self):
        return True if self.approval is not None else False


class EvalModel(Base):
    __tablename__ = 'eval'

    image = db.Column(db.String, nullable=False, default=STATIC_REL+'black_image.png')
    link = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False, default='Text')
    title = db.Column(db.String, nullable=False, default='Title')
    subt = db.Column(db.String, nullable=False, default='Subtitle')
    alignments = db.relationship('PredAlignment', backref='eval', cascade="all, delete-orphan", lazy=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=False)
    restrictions = db.Column(db.String, nullable=False, default="")

    def __init__(self, image, link, text, title, subtitle, restrictions):
        self.link = link
        self.text = text
        self.title = title
        self.subt = subtitle
        self.restrictions = restrictions
        if os.path.exists(image):
            self.image = image

    def __repr__(self):
        return '<Eval %d>' % self.id

    def add_aems(self, aems):
        if not isinstance(aems, list):
            self.alignments.append(aems)
            db.session.add(self)
        else:
            self.alignments.extend(aems)
            db.session.add(self)

    def has_aems(self):
        return self.alignments != []

    def was_eval(self):
        for aem in self.alignments:
            if not aem.was_eval():
                return False
        return True


class Batch(Base):
    __tablename__ = 'batch'

    name = db.Column(db.String, nullable=False, default=str(db.func.current_timestamp()))
    eval = db.relationship('EvalModel', backref='batch', cascade="all, delete-orphan", lazy=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Batch %r>' % self.name

    def add_em(self, ems):
        """
        Add EvalModel object
        :param ems: EvalModel Object(s)
        """
        if not isinstance(ems, list):
            self.eval.append(ems)
        else:
            self.eval.extend(ems)

    def was_eval(self):
        for em in self.eval:
            if not em.was_eval():
                return False

        return True

    def save(self):
        db.session.add(self)
        db.session.commit()
