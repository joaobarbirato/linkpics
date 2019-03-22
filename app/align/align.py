"""
    Register every alignment occurred, as well as it's elements
    @author: João Gabriel Melo Barbirato
"""
from app.VC.boundingBox import BoundingBox


def _add(list_object, element):
    if list_object is None:
        list_object = [element]
    elif isinstance(list_object, list):
        list_object.append(element)
    else:
        list_object = [list_object, element]
    return list_object


class Alignment:
    """
    main class
    """

    def __init__(self, bounding_box, term, mwe=None, syns=None, is_ne=False, html_color=None, img_color=None):
        self.term = term
        self.is_ne = is_ne

        # 1:n alignment
        self.list_bounding_box = bounding_box
        self.occurrence = 1 if isinstance(self.list_bounding_box, BoundingBox) else len(bounding_box)

        # multi-word expressions
        self.list_mwe = mwe
        self.has_mwe = self.list_mwe is not None

        # n:1 alignment
        self.list_syns = syns
        self.has_syns = self.list_syns is not None

        self.html_color = html_color
        self.img_color = img_color

    def add_occurrence(self, bounding_box=None):
        """
        Add occurrence to an alignment
        :param bounding_box: bounding box to a new occurrence
        :return: a list of all bounding boxes connected to self.term
        """
        if bounding_box is not None:
            self.list_bounding_box = _add(self.list_bounding_box, bounding_box)
            self.occurrence = len(self.list_bounding_box)
            return self.list_bounding_box

    def add_mwe(self, mwe=None):
        """
        Add mwe to an alignment
        :param mwe: multi-word expression containing self.term
        :return: a list of all multi-word expressions
        """
        if mwe is not None:
            self.list_mwe = _add(self.list_mwe, mwe)
            self.has_mwe = self.list_mwe is not None
            return self.list_mwe

    def add_syn(self, syn=None):
        """
        Add syn to an alignment
        :param syn: synonym of self.term
        :return: a list of all synonyms
        """
        if syn is not None:
            self.list_syns = _add(self.list_syns, syn)
            self.has_syns = self.list_syns is not None
            return self.list_syns

    def is_syn(self, syn=None):
        """
        Inform if a given term is synonym of self.term
        :param syn: given term
        :return: true if it is, false if it isn't
        """
        return [_syn for _syn in self.list_syns if _syn == syn] != [] if self.list_syns is not None else False

    def __str__(self):
        return self.term


class AllAlignments:
    def __init__(self):
        self.list_alignments = []

    def _query_term(self, x):
        return [algn for algn in self.list_alignments if
                algn.term == x or algn.is_syn(x) or (algn.is_ne and x in algn.term)]

    def add_alignments(self, alignment=None):
        if alignment is not None:
            if isinstance(alignment, Alignment):
                if not self._query_term(alignment.term):
                    self.list_alignments.append(alignment)

            elif isinstance(alignment, list):
                for a in alignment:
                    if not self._query_term(a.term):
                        self.list_alignments.append(a)

            return self.list_alignments

    def get_alignment(self, term=None):
        return self._query_term(term)[0]

    def has_alignment(self, term=None):
        if term is not None:
            return self._query_term(term) != []

    def get_list_terms(self):
        return [algn.term for algn in self.list_alignments]


def init():
    global ALIGNMENTS
    ALIGNMENTS = AllAlignments()
