"""
    Classe wrapper para AMR_AS_GRAPH
    @author: João Gabriel Melo Barbirato
"""

import os
import subprocess
import penman

from app.src.UTIL.corenlp import CoreNLPWrapper
from config import BASE_DIR, TMP_DIR

_TRAIN_FROM = 'scratch/s1544871/model/gpus_0valid_best.pt'


def get_amr_from_snt(snt, amr_list):
    return next((amr for amr in amr_list if amr.snt == snt or snt in amr.snt or amr.snt in snt), None)


class AMRWrapper:
    def __init__(self, snt, token, lemma, pos, ner):
        self.snt = snt
        self.token = token
        self.lemma = lemma
        self.ner = ner
        self.pos = pos
        self.nodes = {}
        self.edges = []
        self.penman = None

    def _get_node_val(self, var=None):
        if var is not None:
            for _var, _value in self.nodes.items():
                if var == _var:
                    return _value

    def build_ne_nodes(self):
        for var, val in self.nodes.items():
            if val == "name":
                _val_buffer = ""
                for edge in self.edges:
                    if edge['parent'] == var:
                        _val_buffer += self._get_node_val(var=edge['node']) + " "

                self.nodes[var] = _val_buffer[:-1]
        pass

    def add_node(self, line=None):
        line_split = line.split(' ')[1].replace('"', '').split('\t')
        self.nodes[line_split[1]] = line_split[2]
        # self.nodes.append(
        #     (line_split[1], line_split[2])
        # )

    def add_edge(self, line=None):
        line_split = line.split(' ')[1].replace('"', '').split('\t')
        # named entity
        if line_split[1] == "name" and ":op" in line_split[2]:
            self.edges.append({
                'label': line_split[2],
                'node': line_split[5],
                'parent': line_split[4]
            })
        else:
            self.edges.append({
                'label': line_split[2],
                'node': line_split[4],
                'parent': line_split[5]
            })

    def set_penman(self, penman_notation):
        self.penman = penman_notation

    def get_penman(self, return_type='str'):
        if return_type == 'str':
            return penman.encode(self.penman)

    def is_node(self, value=None):
        if value is not None:
            for _, node_value in self.nodes.items():
                if node_value == value:
                    return True

        return False


def parse_to_amr_list(snts=None):
    os.chdir(BASE_DIR + "/app/src/amr/AMR_AS_GRAPH_PREDICTION")
    input_dir = TMP_DIR + '/input.txt'
    with open(input_dir, 'w+') as input_file:
        for snt in snts:
            input_file.write("%s\n" % snt)
    a = subprocess.Popen('pwd', stdout=subprocess.PIPE)
    print(a.communicate()[0])
    corenlp = CoreNLPWrapper()

    corenlp.start_base()

    do_dot_py = 'python do.py -train_from ' + _TRAIN_FROM + ' -input ' + input_dir

    snt_to_txt = subprocess.Popen(
        do_dot_py.split(),
        stdout=subprocess.PIPE
    )
    snt_to_txt.wait()
    corenlp.terminate_base()
    amr_list = []

    with open(TMP_DIR + '/input.txt_parsed', 'r') as output_file:
        # AMR_AS_GRAPH_PREDICTION will always end a generated '_parsed' file with \n\n\n
        outputs = output_file.read().split('\n\n')[:-1]
    for output in outputs:
        penman_notation = []
        if output != " " and output != "  " and output is not None:
            output_split = output.split('\n')
            amr_graph = AMRWrapper(
                snt=' '.join(output_split[0].split(' ')[2:]),
                token=output_split[1].split(' ')[2:],
                lemma=output_split[2].split(' ')[2:],
                pos=output_split[3].split(' ')[2:],
                ner=output_split[4].split(' ')[2:],
            )

            for line in output_split[4:]:
                if len(line) > 0:
                    if "node" in line.split(' ')[1]:
                        amr_graph.add_node(line)
                    elif "edge" in line.split(' ')[1]:
                        amr_graph.add_edge(line)
                    elif "ner" not in line.split(' ')[1]:
                        penman_notation.append(line)

            penman_string = ''.join(penman_notation).replace('\n', '')
            penman_graph = penman.decode(penman_string)

            amr_graph.set_penman(penman_graph)
            amr_graph.build_ne_nodes()
            amr_list.append(amr_graph)

    os.chdir(BASE_DIR)
    return amr_list


if __name__ == "__main__":
    snt = ['The marble is white']
    amrs = parse_to_amr_list(snts=snt)
    print(amrs[0].nodes)
    print(amrs[0].edges)
    print(amrs[0].nodes['n7'])
