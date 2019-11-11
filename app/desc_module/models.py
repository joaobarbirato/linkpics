from app import db
from app.align_module.base_model import Sentence
from app.amr_module.models import create_amrmodel, AMRModel
from app.model_utils import BaseModel, _add_relation


from app.eval_module.desc_models import DescBatch, DescEval


class Description(BaseModel):
    __tablename__ = 'description'
    method = db.Column(db.String)
    text = db.Column(db.String)
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


def create_description(text, method):
    return Description(text=text, method=method)
