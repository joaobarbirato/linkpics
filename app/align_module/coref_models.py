from app import db
from app.align_module.base_model import Sentence
from app.model_utils import BaseModel, _add_relation
from app.src.PLN.coreference import Mention


class MentionModel(BaseModel):
    __tablename__ = 'mention_model'
    tokens = db.relationship('Token', backref='mention_model')
    start = db.Column(db.Integer, nullable=True)
    end = db.Column(db.Integer, nullable=True)
    head = db.Column(db.Integer, nullable=True)
    coreference_id = db.Column(db.Integer, db.ForeignKey('coreference_model.id'), nullable=False)

    def __init__(self, start, end, head, tokens):
        """

        :type end: int
        :type start: int
        :type head: int
        :param start:
        :param end:
        :param head:
        """
        self.start = start
        self.end = end
        self.head = head
        self.tokens = tokens


class CoreferenceModel(BaseModel):
    __tablename__ = 'coreference_model'
    mentions = db.relationship('MentionModel', single_parent=True, backref='coreference_model', lazy=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=True)

    def __init__(self, mentions=None, news_sentences_models=None):
        """

        :param mentions:
        """
        if mentions is not None:
            if all(isinstance(m, MentionModel) for m in mentions):
                self.mentions = _add_relation(self.mentions, mentions)
            elif all(isinstance(m, Mention) for m in mentions) and news_sentences_models is not None:
                self.mentions = _add_relation(self.mentions, [MentionModel(
                    start=m.start, end=m.end, head=m.head,
                    tokens=news_sentences_models[m.sentence - 1].get_tokens(m.start, m.end)) for m in mentions]
                )

    def add_mention(self, mention):
        """

        :param mention:
        :return:
        """
        if mention is not None and mention:
            if self.mentions is not None or mention not in self.mentions:
                self.mentions = _add_relation(self.mentions, mention)
        return self.mentions
