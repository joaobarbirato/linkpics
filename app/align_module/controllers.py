import shutil
from flask import Blueprint, render_template, request, json
from flask_login import login_required

from app.src.align.align_tool import AlignTool
from app.src.idg.align_tool_descr import AlignToolDescr

from app import app
from config import STATIC_REL

mod_align = Blueprint('align', __name__, url_prefix='/')


def render_index(action=None):
    return render_template('align_module/index.html', form_action=action, button="Alinhamento Texto Imagem")


@mod_align.route("/")
def main():
    return render_index(action='/alinhamento')


@mod_align.route("/baseline")
@login_required
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


from app.src.util.crawlers.crawler_bbc import Crawler as crawler_bbc
from app.src.util.crawlers.crawler import Crawler as crawler_folha


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

    try:
        result_pessoas, result_objetos, img_url, titulo, legenda, texto, dic_avaliacao, grupo, _ = alinhador.align_from_url(
            _link, _experimento_pessoa, _experimento_objeto)

        if img_url != '':
            shutil.copy2(STATIC_REL + 'alinhamento2.jpg', img_url)

        response = dict(result_pessoas=result_pessoas,
                        result_objetos=result_objetos,
                        img_alinhamento=img_url.replace(STATIC_REL, 'static/'),
                        texto=texto,
                        legenda=legenda,
                        titulo=titulo,
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
    except Exception as e:
        print(f'[{__file__}] : {str(e)}')
        return app.response_class(
            response={'message': f'{str(e)}'},
            status=600,
            mimetype='application/json'
        )



