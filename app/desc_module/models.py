from app import db
from app.align_module.base_model import Sentence
from app.amr_module.models import create_amrmodel, AMRModel
from app.model_utils import BaseModel, _add_relation


from app.eval_module.desc_models import DescBatch, DescEval


class Description(BaseModel):
    __tablename__ = 'description'

    METHOD_TABLE = {
        'baseline4|0': 'Model1',
        'baseline5|0': 'Model2',
        'baseline4|1': 'Model3',
        'baseline5|1': 'Model4',
        'baseline4|2': 'Model5',
        'baseline5|2': 'Model6',
    }

    method = db.Column(db.String)
    text = db.Column(db.String)
    used_focus = db.Column(db.String, nullable=True)
    amr_list = db.relationship('AMRModel', single_parent=True, lazy=True, backref='description',
                               cascade="all, delete-orphan")
    alignment_id = db.Column(db.Integer, db.ForeignKey('alignment.id'), nullable=True)
    desc_eval_id = db.Column(db.Integer, db.ForeignKey('desc_eval.id'), nullable=True)

    def __init__(self, text, method):
        self.text = text
        self.method = method

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text

    def __hash__(self):
        return hash(self.text)

    def add_amr(self, amr):
        return _add_relation(self.amr_list, amr)

    def keep_amr(self, main, adj_list):
        self.add_amr(main)
        self.add_amr(adj_list)

    def get_amr(self):
        return self.amr_list[0]

    def get_main(self):
        return self.amr_list[1]

    def get_adjacents(self):
        return self.amr_list[2:]

    def get_alignment(self):
        return self.alignment

    def get_news(self):
        return self.alignment.sentences()[0].news

    def get_method(self):
        return self.METHOD_TABLE[self.method]

    def set_used_focus(self, value):
        if isinstance(value, str):
            self.used_focus = value
        elif isinstance(value, list):
            self.used_focus = '|'.join(value)

        return self.used_focus


def create_description(text, method):
    return Description(text=text, method=method)
