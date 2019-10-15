"""
    Classe wrapper para AMR_AS_GRAPH
    @author: João Gabriel Melo Barbirato
"""

import os
import subprocess
from os.path import join, isfile

import penman

from app.amr_module.models import AMRModel
from app.src.util.corenlp import CoreNLPWrapper
from config import BASE_DIR, TMP_DIR, SHELL_DIR, SRC_DIR

_TRAIN_FROM = 'scratch/s1544871/model/gpus_0valid_best.pt'


def penman_to_text(amr_list):
    """

    :param amr_list:
    :return:

    :type amr_list: list
    """
    _penman_to_simplify = []
    if not amr_list:
        return _penman_to_simplify

    if isinstance(amr_list[0], AMRModel):
        _penman_to_simplify = [amr.get_penman(return_type='str', indent=False) for amr in amr_list]
    elif isinstance(amr_list[0], str):
        _penman_to_simplify = amr_list

    _file_name = 'snts'
    _file_path = f'{TMP_DIR}/{_file_name}.amr'
    # _penman_to_simplify = [penman.encode(element, indent=False) for element in _penman_to_simplify]

    with open(_file_path, 'w') as amr_file:
        for pts in _penman_to_simplify:
            amr_file.write(f'{pts}\n')

    # anonymize written amr
    amr_simplify_shell = subprocess.Popen(f'{SHELL_DIR}/amr-simplify.sh {BASE_DIR} {_file_path}'.split(), stdout=subprocess.PIPE)
    amr_simplify_shell.communicate()

    # read anonymized amr
    anonimized_amr = open(f'{_file_path}.anonymized', 'r').readlines()

    # anonymized amr to JSON format
    amr_json_list = []
    _json_file_name = f'{_file_name}.amr'
    _json_file_path = f'{TMP_DIR}/{_json_file_name}.json'

    for i, amr in enumerate(amr_list):
        json_cell = {
            "amr": anonimized_amr[i],
            "id": str(i),
            "sent": ""
        }
        amr_json_list.append(json_cell)

    with open(_json_file_path, 'w') as json_file:
        formated_list = str(amr_json_list).replace("'", "\"")
        json_file.write(f'{formated_list}\n')

    # run amr-to-seq
    amr_to_snt_shell = subprocess.Popen(f'{SHELL_DIR}/amr-to-snt.sh {BASE_DIR} {_json_file_path}'.split(), stdout=subprocess.PIPE)
    amr_to_snt_shell.communicate()

    # read generated sequences
    full_sequences = open(f'{_json_file_path}.tok', 'r').read().split("--------\n========\n")[:-1]
    sequences = [seq.split('\n')[2].replace('</s>', '') for seq in full_sequences]

    return sequences


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

    def __repr__(self):
        return penman.encode(self.penman, indent=False)

    def __str__(self):
        return penman.encode(self.penman, indent=False)

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
        elif return_type == 'graph':
            return self.penman

    def is_node(self, value=None):
        if value is not None:
            for _, node_value in self.nodes.items():
                if node_value == value:
                    return True

        return False


def parse_to_amr_list(snts=None):
    os.chdir(f"{BASE_DIR}/{SRC_DIR}amr/AMR_AS_GRAPH_PREDICTION")
    input_dir = TMP_DIR + '/input.txt'
    with open(input_dir, 'w+') as input_file:
        for snt in snts:
            input_file.write("%s\n" % snt)
    a = subprocess.Popen('pwd', stdout=subprocess.PIPE)
    print(a.communicate()[0])
    corenlp = CoreNLPWrapper()

    corenlp.start_base()

    crdir = os.getcwd()
    onlyfiles = [f for f in os.listdir(crdir) if isfile(join(crdir, f))]
    do_dot_py = f'{BASE_DIR}/venv/bin/python3 do.py -train_from {_TRAIN_FROM} -input {input_dir}'

    snt_to_txt = subprocess.Popen(do_dot_py.split())
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


def __test_parse_to_amr_list():
    snt = ['The marble is white']
    amrs = parse_to_amr_list(snts=snt)
    print(amrs[0].nodes)
    print(amrs[0].edges)
    print(amrs[0].nodes['n7'])


if __name__ == "__main__":
    # [a] = penman_to_text(['(a24 / and :op1 (f16 / frame-06 :ARG1 (l15 / landscape :ARG1-of (b17 / blather-01 :ARG1 (o18 / organization :name (n19 / name :op1 "Planalto" :op2 "Palace") :location (s23 / side :ARG1-of (l22 / left-19)) :wiki -)))) :op2 (f32 / follow-01 :ARG0 (p30 / person :ARG0-of (p31 / protest-01 :ARG0 (p6 / person :ARG0-of (c5 / champion-01 :ARG1 (g1 / game :name (n2 / name :op1 "Olympic") :wiki "Olympic_Games") :ARG1 (b4 / ball-01)) :name (n7 / name :op1 "Fabiana" :op2 "Claudino") :ARG0-of (r10 / run-01 :ARG1 (h11 / hold-01 :ARG1 (t12 / torch)) :op1-of (a13 / and :op2 (a14 / around))) :ARG0-of h11 :quant 2 :wiki -)) :ARG0-of (s34 / scream-01 :ARG0 (a33 / athlete)))) :op2 (g25 / government-organization :name (n26 / name :op1 "National" :op2 "Congress") :ARG1-of (r29 / right-05) :wiki "National_Congress_of_the_Communist_Party_of_China"))'])
    [a] = penman_to_text(
        ['(p30 / person :ARG0-of (p31 / protest-01 :ARG0 (p6 / person :name (n7 / name :op1 "Fabiana" :op2 "Claudino") :wiki - :ARG0-of (r10 / run-01 :ARG1 (h11 / hold-01 :ARG1 (t12 / torch)) :op1-of (a13 / and :op2 (a14 / around))) :ARG0-of h11 :quant 2 :ARG0-of (c5 / champion-01 :ARG1 (b4 / ball-01) :ARG1 (g1 / game :name (n2 / name :op1 "Olympic") :wiki "Olympic_Games")))) :ARG0-of (s34 / scream-01 :ARG0 (a33 / athlete)))',
         '(p6 / person :name (n7 / name :op1 "Fabiana" :op2 "Claudino") :wiki - :ARG0-of (r10 / run-01 :ARG1 (h11 / hold-01 :ARG1 (t12 / torch)) :op1-of (a13 / and :op2 (a14 / around))) :ARG0-of h11 :quant 2 :ARG0-of (c5 / champion-01 :ARG1 (b4 / ball-01) :ARG1 (g1 / game :name (n2 / name :op1 "Olympic") :wiki "Olympic_Games")) :ARG0-of (p31 / protest-01 :ARG0 (p30 / person :ARG0-of (s34 / scream-01 :ARG0 (a33 / athlete)))))']
    )
    print(a)
