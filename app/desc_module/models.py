from app import db
from app.align_module.base_model import Sentence


def create_description(text, method):
    return Description(text, method)


class Description(Sentence):
    __tablename__ = 'description'
    method = db.Column(db.String, nullable=False)

    alignment_id = db.Column(db.Integer, db.ForeignKey('alignment.id'), nullable=True)

    def __int__(self, text, method):
        """
        :param text:
        :param method:
        :return:
        """
        self.method = method
        super().__init__(text, label='description')
