"""
    Classe wrapper para AMR_AS_GRAPH
    @author: João Gabriel Melo Barbirato
"""

import subprocess
import os

from amr.parser.AMRProcessors import *
from amr.src.train import read_dicts
from amr.src.parse import generate_parser

from time import sleep

__CORENLP_REL_PATH = 'stanford-corenlp-full-2018-10-05'
_CORENLP_START_SHELL_COMMAND = '/usr/bin/bash start-corenlp-server.sh ' + os.path.join(
    os.path.dirname(os.path.abspath(__file__)), __CORENLP_REL_PATH)
_CORENLP_STOP_SHELL_COMMAND = '/usr/bin/bash stop-corenlp-server.sh'
__TRAIN_FROM = 'scratch/s1544871/model/gpus_0valid_best.pt'


class CoreNLPWrapper():
    def __init__(self):
        self._subprocess = subprocess.Popen(_CORENLP_START_SHELL_COMMAND.split(' '))
        sleep(5)

    def terminate(self):
        self._subprocess = subprocess.Popen(_CORENLP_STOP_SHELL_COMMAND.split(' '))
        sleep(5)


class AMRWrapper:
    def __init__(self, token, lemma, pos, ner):
        self.token = token
        self.lemma = lemma
        self.ner = ner
        self.nodes = []
        self.edges = []

    def add_node(self, line=None):
        line_split = line.split(' ')[1].split('\t')
        self.nodes.append(
            (line_split[1], line_split[2])
        )

    def add_edge(self, line=None):
        line_split = line.split(' ')[1].split('\t')
        self.edges.append({
            'label': line_split[2],
            'node': line_split[4],
            'parent': line_split[5]
        })

    def is_node(self, value=None):
        if value is not None:
            for (_, node_value) in self.nodes:
                if node_value == value:
                    return True

        return False


def parse_to_amr_list(snts=None):
    corenlp = CoreNLPWrapper()

    opt = generate_parser().parse_args()
    opt.lemma_dim = opt.dim
    opt.high_dim = opt.dim
    opt.input = snts
    opt.cuda = None
    opt.gpus[0] = -1

    opt.train_from = __TRAIN_FROM

    dicts = read_dicts()
    print(opt)
    Parser = AMRParser(opt, dicts)
    amr_list = []

    if opt.input:
        # Raw AMR
        outputs = Parser.parse_batch(snts)
        for output in outputs:
            output_split = output.split('\n')
            amr = AMRWrapper(
                token=output_split[0].split(' ')[2:],
                lemma=output_split[1].split(' ')[2:],
                pos=output_split[2].split(' ')[2:],
                ner=output_split[3].split(' ')[2:],
            )

            for line in output_split[3:]:
                if len(line) > 0:
                    if "node" in line.split(' ')[1]:
                        amr.add_node(line)
                    elif "edge" in line.split(' ')[1]:
                        amr.add_edge(line)

            amr_list.append(amr)

    corenlp.terminate()
    return amr_list


if __name__ == "__main__":
    snt = ['The marble is white']
    [amr] = parse_to_amr_list(snts=snt)
    print(amr.token)
    print(amr.lemma)
    print(amr.ner)
    print(amr.nodes)
    print(amr.edges)
