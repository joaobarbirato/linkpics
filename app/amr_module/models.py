"""
    AMR database model
"""
import penman as pm
from app import (db)
from app.model_utils import BaseModel, _add_relation


class Triple(BaseModel):
    __tablename__ = 'triple'
    source = db.Column(db.String, nullable=False, default='')
    relation = db.Column(db.String, nullable=False, default='')
    target = db.Column(db.String, nullable=False, default='')
    graph_id = db.Column(db.Integer, db.ForeignKey('graph.id'), nullable=False)

    def __init__(self, src, rel, tgt):
        self.source = src
        self.relation = rel
        self.target = tgt

    def __repr__(self):
        return self.source, self.relation, self.target


class Graph(BaseModel):
    __tablename = 'graph'
    list_triples = db.relationship('Triple', backref='graph', lazy=True)
    top = db.Column(db.String, nullable=False, default='')
    amr_model_id = db.Column(db.Integer, db.ForeignKey('amr_model.id'), nullable=False)

    def __repr__(self):
        return self.list_triples

    def get_top(self):
        return self.top

    def get_triples(self):
        return self.list_triples

    def set_top(self, new_top):
        """

        :type new_top: str
        :param new_top:
        :return:
        """
        self.top = new_top
        return new_top

    def add_triple(self, triple):
        """
        Add triple to a graph
        :type triple: Triple
        :param triple: triple object
        :return: list of all triples
        """
        if triple is not None and triple:
            if self.list_triples is None or triple not in self.list_triples:
                self.list_triples = _add_relation(self.list_triples, triple)

        return self.list_triples


def penman_to_model(pmn):
    """

    :type pmn: pm.Graph
    :param pmn:
    :return:
    """
    all_triples = pmn.triples()
    list_triple_model = [Triple(src=t[0], rel=t[1], tgt=t[2]) for t in all_triples]
    graph = Graph(list_triples=list_triple_model)
    graph.set_top(pmn.top)
    return graph


class AMRModel(BaseModel):
    __tablename__ = 'amr_model'
    penman = db.Column(db.String, nullable=False, default='')
    graph = db.relationship('Graph', single_parent=True, backref='amr_model', lazy=True, uselist=False)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'), nullable=False)

    def __init__(self, **kwargs):
        """

        :param kwargs:
            - string
            - graph

            - object
        """
        if kwargs:
            if len(kwargs) == 2 and ('string' and 'graph') in kwargs:
                self.penman = kwargs['string']
                self.graph = kwargs['graph']
            elif len(kwargs) == 1 and 'object' in kwargs:
                self.penman = pm.encode(kwargs['object'], top=kwargs['object'].top)
                self.graph = penman_to_model(kwargs['object'])

    def __repr__(self):
        return self.penman

    def get_penman(self, return_type='object'):
        if return_type == 'object':
            return pm.decode(self.penman)
        elif return_type == 'str':
            return self.penman

    def set_graph(self, graph):
        """
        :type graph: Graph
        :param graph: graph object
        :return graph
        """
        if graph is not None:
            self.graph = graph

        return self.graph