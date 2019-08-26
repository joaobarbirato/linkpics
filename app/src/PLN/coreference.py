"""
    Coreference resolver classes
    @author: João Gabriel Melo Barbirato
"""


class Mention:
    def __init__(self, sentence=-1, start=-1, end=-1, head=-1, text=None):
        self.sentence = int(sentence)
        self.start = int(start)
        self.end = int(end)
        self.head = int(head)
        self.text = text

    def set_attr(self, name, value):
        self.__setattr__(name, value)

    def __repr__(self):
        return self.text

    def __str__(self):
        return self.text


class Coreference:
    def __init__(self, mentions=None):
        if mentions is None:
            mentions = []
        self.mentions = mentions

    def add_mention(self, mention):
        self.mentions.append(mention)


class CoreferenceDocument:
    def __init__(self, sentences=None, coreferences=None):
        """
        """
        if coreferences is None:
            coreferences = []

        self.coreferences = coreferences

        if sentences is None:
            sentences = []
        self.sentences = sentences

    def add_coref(self, coref):
        self.coreferences.append(coref)

    def load_dict(self, coref_dict, sentences):
        assert isinstance(coref_dict, dict)
        self.sentences = sentences
        for coref, mention in coref_dict.items():
            current_coref = Coreference()
            for mention, items in mention.items():
                current_mention = Mention()
                for item, value in items.items():
                    print(item, value)
                    if item != 'text':
                        current_mention.set_attr(item, int(value))
                    else:
                        current_mention.set_attr(item, str(value))
                current_coref.add_mention(mention=current_mention)

            self.add_coref(coref=current_coref)

    def get_coref_terms(self):
        return [[mention for mention in cref.mentions] for cref in self.coreferences]

    def get_sentences(self):
        return self.sentences
