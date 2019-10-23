from app import db
from app.align_module.base_model import Sentence


def create_description(text, method):
    return Description(text, method)


class Description(Sentence):
    __tablename__ = 'description'
    method = db.Column(db.String)

    alignment_id = db.Column(db.Integer, db.ForeignKey('alignment.id'), nullable=True)
    # description_eval_id = db.Column(db.Integer, db.ForeignKey('description_eval.id'), nullable=True)
    main_amr = ''
    adjacent_amr_list = []

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

    def keep_amr(self, main, adj_list):
        self.main_amr = main
        self.adjacent_amr_list = adj_list
