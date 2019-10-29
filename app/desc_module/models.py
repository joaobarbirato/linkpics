from app import db
from app.align_module.base_model import Sentence
from app.amr_module.models import create_amrmodel, AMRModel
from app.model_utils import BaseModel, _add_relation


def create_description(text, method):
    return Description(text, method)


def create_amrgroup():
    return AMRGroup()


class AMRGroup(BaseModel):
    __tablename__ = 'amr_group'
    amr_list = db.relationship('AMRModel', single_parent=True, lazy=True, backref='amr_group')
    description_id = db.Column(db.Integer, db.ForeignKey('sentence.id'), nullable=True)

    def __init__(self):
        pass

    def add_amr(self, amr):
        if amr is not None or amr:
            if isinstance(amr, AMRModel):
                self.amr_list = _add_relation(self.amr_list, create_amrmodel(copy=amr))
            elif isinstance(amr, list):
                self.amr_list = _add_relation(self.amr_list, [create_amrmodel(copy=a) for a in amr])

        return self.amr_list

    def get_first(self):
        return self.amr_list[0]

    def get_others(self):
        return self.amr_list[1:]


class Description(Sentence):
    __tablename__ = 'description'
    method = db.Column(db.String)
    alignment_id = db.Column(db.Integer, db.ForeignKey('alignment.id'), nullable=True)
    derivated_amr = db.relationship('AMRGroup', uselist=False, single_parent=True, lazy=True, backref='description')

    __mapper_args = {
        'polymorphic_identity': 'sentence'
    }

    def __int__(self, text, method):
        """
        :param text:
        :param method:
        :return:
        """
        self.method = method
        super().__init__(text, label='description')

    def add_amrgroup(self, amr_group):
        self.derivated_amr = amr_group
        return self.derivated_amr

    def keep_amr(self, main, adj_list):
        self.derivated_amr.add_amr(main)
        self.derivated_amr.add_amr(adj_list)

    def get_main(self):
        return self.derivated_amr.get_first()

    def get_adjacents(self):
        return self.derivated_amr.get_others()
