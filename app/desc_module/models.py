from app.align_module.base_model import Sentence


class Description(Sentence):
    def __int__(self, text):
        super().__init__(text)