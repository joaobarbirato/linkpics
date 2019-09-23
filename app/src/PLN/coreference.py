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

    def get_mentions(self):
        return self.mentions


class CoreNLPToken:
    def __init__(self, dictionary):
        self.word = dictionary['word']
        self.lemma = dictionary['lemma']
        self.pos = dictionary['pos']
        self.ner = dictionary['ner']
        self._dictionary = dictionary

    def __repr__(self):
        return self.word

    def __str__(self):
        return self.word

    def marshal(self):
        return self._dictionary


class CoreferenceDocument:
    def __init__(self, sentences=None, coreferences=None):
        """

        :param sentences:
        :param coreferences:
        """
        if coreferences is None:
            coreferences = []

        self.coreferences = coreferences
        self.tkn_snts = None

        if sentences is None:
            sentences = []
        self.sentences = sentences

    def add_coref(self, coref):
        self.coreferences.append(coref)

    def load_dict(self, coref_dict, sentences):
        assert isinstance(coref_dict, dict)
        self.sentences = sentences
        self.tkn_snts = [[CoreNLPToken(tkn) for tkn in snt] for snt in coref_dict['tokenized']]
        for coref, mention in coref_dict.items():
            if 'tokenized' not in coref:
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

    def get_tkn_snts(self):
        return self.tkn_snts

    def get_corefs(self):
        return self.coreferences
