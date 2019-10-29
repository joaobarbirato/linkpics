"""
    AMR database model
"""
import penman as pm
from sqlalchemy.orm.collections import InstrumentedList
from operator import methodcaller

from app import (db)
from app.align_module.base_model import Sentence
from app.model_utils import BaseModel, _add_relation, PrintException, _add_session


def copy_triples_from_list(triple_list):
    return [Triple(src=triple.source, rel=triple.relation, tgt=triple.target) for triple in triple_list]


def organize_triples_list(triples_list, top):
    try:
        if isinstance(top, Triple):
            new_list = InstrumentedList([])
            new_list.append(top)
            for triple in triples_list:
                if triple != top:
                    if triple.relation == 'instance':
                        new_list.insert(1, triple)
                    else:
                        new_list.append(triple)

            return new_list
    except Exception as exc:
        PrintException()


def top_from_triples_list(triples_list, ancestral):
    """

    :type ancestral: AMRModel
    :param triples_list:
    :param ancestral:
    :return:
    """
    instance_list = []
    for t in triples_list:
        if t.is_instance():
            instance_list.append(t)

    distances = []
    for triple in instance_list:
        distance = ancestral.root_distance(triple)
        distances.append(distance)

    minimum = triples_list[distances.index(min(distances))]
    return minimum


def triple_model_list_to_penman(triple_model_list, top_id):
    return pm.encode(pm.Graph(data=[(triple.source, triple.relation, triple.target) for triple in triple_model_list]),
                     top=top_id)


class Triple(BaseModel):
    """
        nodes:
            - source = variable
            - relation = 'instance'
            - target = lemma

        vertex:
            - source = variable of a source node
            - relation = semantic role
            - target = variable of a target node
    """
    __tablename__ = 'triple'
    source = db.Column(db.String, nullable=False, default='')
    relation = db.Column(db.String, nullable=False, default='')
    target = db.Column(db.String, nullable=True, default='')
    amr_model_id = db.Column(db.Integer, db.ForeignKey('amr_model.id'), nullable=False)

    def __init__(self, **kwargs):

        if kwargs:
            if len(kwargs) == 3 and ('src' and 'rel' and 'tgt') in kwargs:
                self.source = str(kwargs['src'])
                self.relation = str(kwargs['rel'])
                self.target = str(kwargs['tgt'])
            if len(kwargs) == 1 and 'copy' in kwargs:
                self.source = str(kwargs['copy'].source)
                self.relation = str(kwargs['copy'].relation)
                self.target = str(kwargs['copy'].target)

    def __repr__(self):
        return f"<AMR Triple ({self.source}, {self.relation}, {self.target})>"

    def __contains__(self, item):
        return self.is_instance(item) or self.is_relation(item)

    def __eq__(self, other):
        """

        :type other: Triple
        :param other:
        :return:
        """
        return self.relation == 'instance' and self.target == other.target

    def __ne__(self, other):
        """

        :type other: Triple
        :param other:
        :return:
        """
        return not self.__eq__(other=other)

    def __hash__(self):
        return hash(f'{self.source}, {self.relation}, {self.target}')

    def is_instance(self, item=''):
        """

        :type item: str
        :param item:
        :return:
        """
        return (self.relation == 'instance' and self.target == item) or '"' in self.target if item != '' else \
            (self.relation == 'instance') or '"' in self.target

    def is_relation(self, item):
        return item == self.relation

    def invert(self):
        if '-of' in self.relation:
            self.relation = self.relation
        else:
            self.relation += '-of'
        aux = self.source
        self.source = self.target
        self.target = aux
        return self


def penman_to_model(pmn):
    """

    :type pmn: pm.Graph
    :param pmn:
    :return:
    """
    all_triples = pmn.triples()
    list_triple_model = [Triple(src=t[0], rel=t[1], tgt=t[2])
                         if not t.inverted else
                         Triple(src=t[2], rel=f'{t[1]}-of', tgt=t[0]) for t in all_triples]
    return list_triple_model, pmn.top


def _match_triple(src=None, relation=None, target=None, triple=None):
    """

    :param src:
    :param relation:
    :param target:
    :param triple:
    :return:
    """

    def __eq_or_in(attr, triple_attr):
        return attr is not None and (attr.upper() == triple_attr.upper() or attr.upper() in triple_attr.upper() or triple_attr.upper() in attr.upper())
    try:
        if triple is None:
            return False

        rule = (relation is None and target is None and (src is not None and src == triple.source))
        rule = rule or (relation is None and __eq_or_in(target, triple.target) and src is None)
        rule = rule or (relation is None and __eq_or_in(target, triple.target) and (src is not None and src == triple.source))
        rule = rule or (__eq_or_in(relation, triple.relation) and target is None and src is None)
        rule = rule or (__eq_or_in(relation, triple.relation) and target is None and (src is not None and src == triple.source))
        rule = rule or (__eq_or_in(relation, triple.relation) and __eq_or_in(target, triple.target) and src is None)
        rule = rule or (__eq_or_in(relation, triple.relation) and __eq_or_in(target, triple.target) and (src is not None and src == triple.source))
        return rule
    except Exception as exc:
        PrintException()


def _common_names(amr1, amr2):
    """

    :type amr1: AMRModel
    :type amr2: AMRModel
    :param amr1:
    :param amr2:
    :return:
    """

    try:
        return_list = set()
        names1 = amr1.get_triples(relation='instance', target='name')
        names2 = amr2.get_triples(relation='instance', target='name')

        names_string_1 = zip(names1, [amr1.get_names(name.source) for name in names1])
        names_string_2 = zip(names2, [amr2.get_names(name.source) for name in names2])

        for name1, string1 in names_string_1:
            for name2, string2 in names_string_2:
                if string1 == string2 or string1 in string2 or string2 in string1:
                    return_list.add((name1, name2, min([len(string1), len(string2)])))

        return InstrumentedList(return_list)
    except Exception as exc:
        PrintException()


def _common_persons(amr1, amr2):
    try:
        return_list = set()
        persons_self = amr1.get_triples(relation='instance', target='person')
        persons_other = amr2.get_triples(relation='instance', target='person')

        person_names_self = zip(persons_self, [amr1.get_triples(src=ps.source, relation='name') for ps in persons_self])
        person_names_other = zip(persons_other,
                                 [amr2.get_triples(src=po.source, relation='name') for po in persons_other])

        for person1, name1 in person_names_self:
            names1 = amr1.get_names(name1.source)
            for person2, name2 in person_names_other:
                names2 = amr2.get_names(name2.source)
                if names1 == names2 or names1 in names2 or names2 in names1:
                    return_list.add((person1, person2))

        return return_list

    except Exception as exc:
        PrintException()


def _delete_nodes(triple_list, node_source):
    from_source = triples(triple_list, src=node_source)
    from_target = triples(triple_list, target=node_source)
    return InstrumentedList(
        set(triple_list) - set(from_source) - set(from_target)
    )


def triples(triples_list, src=None, relation=None, target=None):
    try:
        if src is None and relation is None and target is None:
            return triples_list
        else:
            return_list = InstrumentedList([])
            for triple in triples_list:
                if _match_triple(src, relation, target, triple):
                    return_list.append(triple)
            return return_list
    except Exception as exc:
        PrintException()


def _filter_common(triple_list, person_list, name_list):
    """

    :param triple_list:
    :param person_list:
    :param name_list:
    :return:
    """
    filtered_names = set()
    names = triples(triples_list=triple_list, relation='instance', target='name')
    for name in names:
        for n_tuple in name_list:
            if name.source == n_tuple[0] or name.source == n_tuple[1]:
                filtered_names.add(name)

    filtered_persons = set()
    persons = triples(triples_list=triple_list, relation='instance', target='person')
    for person in persons:
        for p_tuple in person_list:
            if person.source == p_tuple[0] or person.source == p_tuple[1]:
                filtered_persons.add(person)

    return InstrumentedList(
        set(triple_list) - (set(names) - filtered_names) - set(set(persons) - filtered_persons)
    )


def create_amrmodel(**kwargs):
    return AMRModel(**kwargs)


class AMRModel(BaseModel):
    __tablename__ = 'amr_model'
    list_triples = db.relationship('Triple', backref='amr_model', lazy=True)
    top = db.Column(db.String, nullable=False, default='')
    penman = db.Column(db.String, nullable=False, default='')
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'))
    amr_group_id = db.Column(db.Integer, db.ForeignKey('amr_group.id'), nullable=True)

    def __init__(self, **kwargs):
        """

        :param kwargs:
            - string
            - triples
            - top

            - object

            -copy
        """
        if kwargs:
            if len(kwargs) == 3 and ('string' and 'triples' and 'top') in kwargs:
                self.penman = kwargs['string']
                self.list_triples = kwargs['graph']
                self.top = kwargs['top']

            elif len(kwargs) == 2 and ('triples' and 'top') in kwargs:
                self.top = kwargs['top']
                self.list_triples = kwargs['triples']
                self.penman = triple_model_list_to_penman(self.list_triples, top_id=self.top)

            elif len(kwargs) == 1 and 'object' in kwargs:
                self.penman = pm.encode(kwargs['object'], top=kwargs['object'].top)
                self.list_triples, self.top = penman_to_model(kwargs['object'])

            elif len(kwargs) == 1 and 'copy' in kwargs:
                _source_amr: AMRModel = kwargs['copy']
                self.list_triples = InstrumentedList([Triple(copy=t) for t in _source_amr.get_triples()])
                self.penman = _source_amr.get_penman(return_type='str')
                self.top = _source_amr.get_top()

    def __repr__(self):
        return self.penman

    def __str__(self):
        return self.penman

    def __eq__(self, other):
        if isinstance(other, AMRModel):
            return all(triple in other.get_triples() for triple in self.list_triples) and all(triple in self.list_triples for triple in other.get_triples())
        elif isinstance(other, str):
            return self.penman == other

    def __hash__(self):
        return hash(self.penman)

    def add(self, other, tuple_ref):
        """

        :type tuple_ref: tuple
        :param tuple_ref:
        :type other: AMRModel
        :param other:
        :return:
        """
        try:
            other_top = other.get_top()
            old_triples = other.get_triples()
            if old_triples:
                new_triples = set()
                for old_triple in old_triples:
                    if old_triple.source == tuple_ref[1]:
                        if old_triple.relation != 'instance':
                            new_triple = Triple(src=tuple_ref[0], rel=old_triple.relation, tgt=old_triple.target)
                            new_triples.add(new_triple)
                    elif old_triple.target == tuple_ref[1]:
                        new_triple = Triple(src=old_triple.source, rel=old_triple.relation, tgt=tuple_ref[0])
                        new_triples.add(new_triple)
                    elif old_triple.is_instance():
                        new_triples.add(old_triple)

                self.list_triples = InstrumentedList(new_triples.union(set(self.list_triples)))
                self.list_triples = organize_triples_list(self.list_triples, self.get_triple(src=self.top, relation='instance'))
                self.penman = triple_model_list_to_penman(self.list_triples, self.top)
            return self.list_triples
        except Exception as exc:
            PrintException()

    def delete(self, node_source):
        if isinstance(node_source, str):
            self.list_triples = _delete_nodes(self.list_triples, node_source)
        elif isinstance(node_source, Triple):
            self.list_triples = _delete_nodes(self.list_triples, node_source.source)

        return self.list_triples

    def get_top(self):
        return self.top

    def get_triples(self, src=None, relation=None, target=None):
        """

        :param src:
        :param relation:
        :param target:
        :return:
        """
        return triples(self.list_triples, src=src, relation=relation, target=target)

    def get_penman(self, return_type='object', indent=None):
        if return_type == 'object':
            return pm.decode(self.penman)
        elif return_type == 'str':
            if indent is None:
                return self.penman
            else:
                return pm.encode(pm.decode(self.penman), top=self.top, indent=indent)

    def has_common_names(self, other):
        return _common_names(self, other)

    def has_common_person(self, other):
        return _common_persons(self, other)

    def set_top(self, new_top):
        """

        :type new_top: str
        :param new_top:
        :return:
        """
        self.top = new_top
        return new_top

    def get_parents(self, node):
        _src = ''
        if isinstance(node, str):
            _src = node
        elif isinstance(node, Triple):
            _src = node.source
        candidates = self.get_triples(target=_src)
        if candidates is not None and candidates:
            candidate = [triple for triple in candidates if triple.target == _src][0]
            parent_node_candidate = self.get_triple(src=candidate.source, relation='instance')
            if '-of' not in candidate.relation and candidate and parent_node_candidate:
                return [Triple(copy=parent_node_candidate), Triple(copy=candidate), Triple(copy=node)]
        return []

    def is_instance(self, item):
        """

        :type item: str
        :param item:
        :return:
        """
        return any(item == triple.source and triple.is_instance() for triple in self.list_triples)

    def get_names(self, name_src):
        ops = self.role(src=name_src)
        if ops:
            return " ".join([op.target for op in ops])
        return []

    def is_name(self, string):
        """

        :type string: str
        :param string:
        :return:
        """
        splitted_string = string.split()
        possible_names = self.get_triples(relation='instance', target='name')
        return_list = InstrumentedList([])
        for possible_name in possible_names:
            possible_name_string_list = self.get_triples(src=possible_name.source, relation='op')
            if possible_name_string_list and all(any(ss in pns.target for ss in splitted_string)
                                                 for pns in possible_name_string_list):
                return_list.append(possible_name)

        return False if not return_list else return_list[0]

    def get_size(self):
        return len([triple for triple in self.list_triples if triple.is_relation('instance')])

    def intersection(self, amr, focus=None):
        """

        :param focus:
        :type amr: AMRModel
        :param amr:
        :return:
        """
        return_list = set()
        if focus is None:
            _other_triples = amr.get_triples()
            for triple in _other_triples:
                if triple in self.list_triples:
                    return_list.add(triple)

        else:
            focus_is_name = amr.is_name(focus)
            if focus_is_name and self.is_name(focus):
                return_list.add(focus_is_name)
            else:
                _other_triples = amr.get_triples(relation='instance', target=focus)
                for triple in _other_triples:
                    if triple in self.list_triples:
                        return_list.add(triple)

        return _filter_common(InstrumentedList(return_list), self.has_common_person(amr),
                              self.has_common_names(amr))

    def get_instance(self, src=None):
        for triple in self.list_triples:
            if triple.source == src and triple.is_instance():
                return triple

    def get_triple(self, src=None, relation=None, target=None):
        try:
            if src is None and relation is None and target is None:
                return None
            if target is not None:
                triple_is_name = self.is_name(target)
                if triple_is_name:
                    return triple_is_name

            for triple in self.list_triples:
                if _match_triple(src, relation, target, triple):
                    return triple
        except Exception as exc:
            PrintException()

    def role(self, src=None, target=None):
        return_list = InstrumentedList([])
        for triple in self.list_triples:
            is_instance = triple.relation == 'instance'
            if not is_instance and (
                    (src is not None and triple.source == src) or
                    (target is not None and triple.target == target)):
                return_list.append(triple)

        return return_list

    def path(self, src, target=None, only_roles=True):
        """
        DFS based
        :param src:
        :param target:
        :param only_roles:
        :return:
        """
        if src == target:
            return []
        _ways = self.role(src=src)
        for way in _ways:
            if way.target == target:
                return InstrumentedList(
                    [way] if only_roles
                    else [self.get_instance(src=src)] + [way] +
                         [self.get_instance(src=target)]
                )
            else:
                new_way = self.path(src=way.target, target=target, only_roles=only_roles)
                if new_way and new_way is not None:
                    return InstrumentedList([way]) + new_way

        return []

    def span(self, top):
        """

        :type top: Triple
        :param top:
        :return:
        """
        # base

        _ways = self.role(src=top.source)
        new_way = InstrumentedList([])
        for way in _ways:
            if self.is_instance(way.target):
                way_instance = self.get_instance(src=way.target)
                new_way += InstrumentedList([way]) + self.span(top=way_instance)
            else:
                new_way.append(way)

        return InstrumentedList([top] + new_way)

    def root_distance(self, triple):
        """

        :type triple: Triple
        :param triple:
        :return:
        """
        path = self.path(src=self.top, target=triple.source, only_roles=True)
        return len(path)

    def get_subgraph(self, top):
        """

        :type top: Triple
        :param top:
        :return:
        """
        try:
            _span = self.span(top=top)
            possible_children = InstrumentedList(set(_span))
            not_instances = []
            instances = []
            for children in possible_children:
                if children.relation != 'instance':
                    not_instances.append(children)
                else:
                    instances.append(children)

            for not_instance in not_instances:
                if all(
                        instance.source != not_instance.source and
                        instance.source != not_instance.target and
                        not_instance != top
                        for instance in instances
                ):
                    possible_children.remove(not_instance)

            possible_children = organize_triples_list(triples_list=possible_children, top=top)
            new_subgraph = AMRModel(top=top.source, triples=copy_triples_from_list(possible_children)) if possible_children else None
            return new_subgraph
        except Exception as exc:
            PrintException()

    def __contains__(self, item):
        return any(item == triple for triple in self.list_triples)

    def save(self):
        [triple.save() for triple in self.list_triples]
        _add_session(self)


def biggest_amr(amrmodel_list):
    try:
        return max([amr for amr in amrmodel_list], key=methodcaller('get_size'))
    except Exception as exc:
        PrintException()
