"""
    Using NetworkX to create visual representations of AMR
    @author: João Gabriel Melo Barbirato
"""
import json

from app import app
from app.src.UTIL.wrapper import parse_to_amr_list
import networkx as nx
import matplotlib.pyplot as plt
from nltk import sent_tokenize

from app.src.UTIL.crawler import Crawler as crawler_folha
from app.src.UTIL.crawler_bbc import Crawler as crawler_bbc, file_to_variavel

from config import STATIC_REL


def generate_digraphs_amr(snt_list=None):
    """
    Generate digraphs from AMR_AS_GRAPH_PREDICTION
    :param snt_list: List of sentences
    :return: a NetworkX digraph for all AMR parsed
    """
    """
    TODO:
        self.add_edges_from(((u, v, {weight: d}) for u, v, d in ebunch_to_add),
            ValueError: not enough values to unpack (expected 3, got 2)

    """
    if snt_list is not None:
        digraphs = {}
        amr_list = parse_to_amr_list(snts=snt_list)
        increment = 0
        for amr in amr_list:
            dg = nx.DiGraph()
            for key, value in amr.nodes.items():
                dg.add_node(key + " / " + value)

            # dg.add_nodes_from(amr.nodes.keys())
            for edge in amr.edges:
                dg.add_edge(
                    edge['parent'] + " / " + amr.nodes[edge['parent']],
                    edge['node'] + " / " + amr.nodes[edge['node']],
                    edge_label=edge['label']
                )

            digraphs[str(increment)] = dg
            pos = nx.kamada_kawai_layout(dg)
            fig = plt.figure(increment)
            nx.draw(dg, pos, node_size=300, node_color='red', with_labels=True, arrows=True)
            nx.draw_networkx_edge_labels(dg, pos=pos, font_color='black', font_size=5, label_pos=0.5)
            plt.savefig(STATIC_REL + "graphs/Graph_%d.png" % increment, format="PNG")
            increment += 1
            plt.close(fig)

        return digraphs


def crawl_link_to_generated_amr(link):
    if "folha" in link:
        crawler = crawler_folha()
    elif "bbc" in link:
        crawler = crawler_bbc()
    else:  # invalid url format
        return app.response_class(
            response=json.dumps({'message': 'Bad request'}),
            status=400,
            mimetype='application/json'
        )
    nome_arquivo, title, _ = crawler.crawl_page(link)
    if title != "":
        text = crawler.file_to_variavel(nome_arquivo).replace(".", ". ").replace("  ", " ")
        subtitle = crawler.file_to_variavel(nome_arquivo + "_caption.txt").replace(".", ". ").replace("  ", " ")
        title = title.replace(".", ". ").replace("  ", " ")

        _text_tokenized = sent_tokenize(text=text)
        _title_tokenized = sent_tokenize(text=title)
        _subtitle_tokenized = sent_tokenize(text=subtitle)

        inc = 0

        def link_to_graph(number, snt, string):
            return string.replace(
                snt, "<a id=\"link_to_" + str(number) + "\" value=\"" + str(number) + "\">" + snt + "</a>"
            )

        for snt in _text_tokenized:
            text = link_to_graph(number=inc, snt=snt, string=text)
            inc += 1

        for snt in _title_tokenized:
            title = link_to_graph(number=inc, snt=snt, string=title)
            inc += 1

        for snt in _subtitle_tokenized:
            subtitle = link_to_graph(number=inc, snt=snt, string=subtitle)
            inc += 1

        snt_list = _text_tokenized + _title_tokenized + _subtitle_tokenized

        generate_digraphs_amr(snt_list=snt_list)

        return dict(
            text=text,
            title=title,
            subtitle=subtitle,
        )


if __name__ == "__main__":
    digraphs = generate_digraphs_amr(
        snt_list=[
            'The quick brown fox jumps over the lazy dog.',
            'The girl made adjustments to the machine',
        ]
    )

