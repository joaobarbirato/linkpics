import shutil
from flask import Blueprint, render_template, request, json
from werkzeug.exceptions import BadRequestKeyError

from app.align_module import models
from app.src.align.align_tool import AlignTool
from app.src.align.align_tool_descr import AlignToolDescr

from app import app
from config import STATIC_REL

mod_align = Blueprint('align', __name__, url_prefix='/')


def render_index(action=None):
    return render_template('align_module/index.html', form_action=action, button="Alinhamento Texto Imagem")


@mod_align.route("/")
def main():
    return render_index(action='/alinhamento')


@mod_align.route("/baseline")
def main_baseline():
    return render_index(action='/alinhamento')


@mod_align.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


# @mod_align.route('/avaliacao', methods=['POST'])
# def salvar_avaliacao():
#     _link = request.form['link']
#
#     _avaliacao = json.loads(request.form['avaliacao'])
#     _medida_similaridade = request.form['medida_similaridade']
#
#     storage = StorageMongo()
#
#     dic_avaliacao = dict(link=_link, avaliacao=_avaliacao)
#
#     id = None
#     #       Similaridade WUP
#     if _medida_similaridade == "wup":
#         id = storage.insert_one(dic_avaliacao, "avaliacoes_wup")
#
#     #     Similaridade Word Embeddings
#     elif _medida_similaridade == "we":
#         id = storage.insert_one(dic_avaliacao, "avaliacoes_we")
#
#     print(id)
#     return '', 200


from app.src.UTIL import Crawler as crawler_bbc
from app.src.UTIL import Crawler as crawler_folha
from app.src.UTIL import utils


@mod_align.route('/alinhamento', methods=['POST'])
def alinhar():
    _link = request.form['link']

    _experimento_pessoa = int(request.form['pessoas']) + 1
    _experimento_objeto = int(request.form['objetos']) + 1

    if "folha" in _link:
        alinhador = AlignTool(crawler=crawler_folha)
    elif "bbc" in _link:
        alinhador = AlignTool(crawler=crawler_bbc)
    else:  # invalid url format
        return app.response_class(
            response=json.dumps({'message': 'Bad request'}),
            status=400,
            mimetype='application/json'
        )

    # try:
    result_pessoas, result_objetos, img_url, titulo, legenda, texto, dic_avaliacao, grupo = alinhador.align_from_url(
        _link, _experimento_pessoa, _experimento_objeto)

    if img_url != '':
        shutil.copy2(STATIC_REL + 'alinhamento2.jpg', img_url)

    # alinhador_descr = AlignToolDescr(
    #     title=alinhador.orig_titulo, sub=alinhador.orig_legenda, text=alinhador.orig_texto, align_group=grupo
    # )

    response = dict(result_pessoas=result_pessoas,
                    result_objetos=result_objetos,
                    img_alinhamento=img_url.replace(STATIC_REL, 'static/'),
                    texto=texto,
                    legenda=legenda,
                    titulo=titulo,
                    descricoes=[],
                    message='',
                    dic_avaliacao=dic_avaliacao)

    print(response)
    print(grupo.get_list_terms())
    return app.response_class(
        response=json.dumps(response),
        status=200,
        mimetype='application/json',
        direct_passthrough=True
    )
    # except Exception as e:
    #     return app.response_class(
    #         response=json.dumps({'message': str(e)}),
    #         status=600,
    #         mimetype='application/json'
    #     )



