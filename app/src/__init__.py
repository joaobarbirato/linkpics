# Carregar Word embeddings
from app.src.PLN.word_embeddings import WordEmbeding

we = WordEmbeding(100)


def init_we():
    we.CarregarWordEmbeddings()


def get_we():
    return we
