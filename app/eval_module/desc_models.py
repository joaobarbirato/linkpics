from app import db
from app.eval_module import Base
from app.model_utils import _add_relation


def get_all_batch_desc():
    return DescBatch.query.all()


def get_filtered_batch_desc(**kwargs):
    return DescEval.query.filter_by(**kwargs)


def get_all_desc_eval():
    return DescEval.query.all()


def create_desc_eval(desc_model):
    return DescEval(desc_model=desc_model)


class DescEval(Base):

    APPROVAL_TABLE = {
        2: "Correto",
        1: "Parcialmente correto",
        0: "Incorreto",
        -1: "Inválido"
    }

    COMPARE_BASELINE_TABLE = {
        0: "Pior",
        1: "Igual",
        2: "Melhor"
    }

    __tablename__ = 'desc_eval'
    desc_model = db.relationship('Description', uselist=False, lazy=True, backref='desc_eval',
                                 cascade="all, delete-orphan")

    approval = db.Column(db.Integer, nullable=True)
    comments = db.Column(db.String, nullable=True)
    compare_baseline = db.Column(db.Integer, nullable=True)

    desc_batch_id = db.Column(db.Integer, db.ForeignKey('desc_batch.id'), nullable=True)

    def __init__(self, desc_model):
        self.desc_model = desc_model

    def __repr__(self):
        return f'<DescEval {self.desc_model}>'

    def __lt__(self, other):
        return f'{self.get_desc().get_alignment().get_term()}{self.get_news().link}' < \
               f'{other.get_desc().get_alignment().get_term()}{other.get_news().link}'

    def approve(self, value):
        """

        :type value: int
        """
        self.approval = value
        return self.approval

    def was_eval(self):
        return self.approval is not None

    def get_desc(self):
        return self.desc_model

    def get_news(self):
        return self.desc_model.get_news()

    def get_approval_string(self):
        """

        :type code: int
        """
        return self.APPROVAL_TABLE[self.approval]

    def set_compare_baseline(self, value):
        self.compare_baseline = value
        return self.compare_baseline

    def get_compare_baseline(self):
        return self.COMPARE_BASELINE_TABLE[self.compare_baseline]

    def get_method(self):
        return self.desc_model.get_method()

    def get_comment(self):
        return self.comments


def create_desc_batch(name):
    return DescBatch(name=name)


class DescBatch(Base):
    __tablename__ = 'desc_batch'
    name = db.Column(db.String, nullable=False)
    desc_eval_list = db.relationship('DescEval', lazy=True, backref='DescBatch', cascade="all, delete-orphan")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'<DescBatch {self.name}>'

    def add_desc_eval(self, desc_eval):
        """

        :type desc_eval: DescEval
        :param desc_eval:
        :return:
        """
        return _add_relation(self.desc_eval_list, desc_eval)

    def was_eval(self):
        return all(desc_eval.was_eval() for desc_eval in self.desc_eval_list)
