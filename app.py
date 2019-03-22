import json
import shutil
from flask import Flask, render_template, json, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequestKeyError

from app.align import align
from app.UTIL import utils
from app.UTIL.storage_mongo import StorageMongo

from app.align.align_tool import AlignTool
from app.align.align_tool_descr import AlignToolDescr

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
CORS(app)


def render_index(action=None):
    return render_template('index.html', form_action=action)


@app.route("/")
def main():
    return render_index(action='/alinhamento')


@app.route("/baseline")
def main_baseline():
    return render_index(action='/alinhamento')


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route('/avaliacao', methods=['POST'])
def salvar_avaliacao():
    _link = request.form['link']

    _avaliacao = json.loads(request.form['avaliacao'])
    _medida_similaridade = request.form['medida_similaridade']

    storage = StorageMongo()

    dic_avaliacao = dict(link=_link, avaliacao=_avaliacao)

    id = None
    #       Similaridade WUP
    if _medida_similaridade == "wup":
        id = storage.insert_one(dic_avaliacao, "avaliacoes_wup")

    #     Similaridade Word Embeddings
    elif _medida_similaridade == "we":
        id = storage.insert_one(dic_avaliacao, "avaliacoes_we")

    print(id)
    return '', 200


from app.UTIL.crawler_bbc import Crawler as crawler_bbc
from app.UTIL import Crawler as crawler_folha


@app.route('/alinhamento', methods=['POST'])
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
        result_pessoas, result_objetos, img_url, titulo, legenda, texto, dic_avaliacao = alinhador.align_from_url(
            _link, _experimento_pessoa, _experimento_objeto)

        if img_url != '':
            shutil.copy2('static/alinhamento2.jpg', img_url)

        alinhador_descr = AlignToolDescr(
            title=alinhador.orig_titulo, sub=alinhador.orig_legenda, text=alinhador.orig_texto
        )

        response = dict(result_pessoas=result_pessoas,
                        result_objetos=result_objetos,
                        img_alinhamento=img_url,
                        texto=texto,
                        legenda=legenda,
                        titulo=titulo,
                        descricoes=alinhador_descr.get_descr(),
                        message='',
                        dic_avaliacao=dic_avaliacao)

        print(response)

        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=600,
            mimetype='application/json'
        )


@app.route('/upload', methods=['POST'])
def alinhamento_livre():
    try:
        file = request.files['choosed_file']
    except BadRequestKeyError:
        return app.response_class(
            response=json.dumps({'message': 'Você deve selecionar um arquivo'}),
            status=400,
            mimetype='application/json'
        )

    file.save('urls.txt')
    urls = utils.file_to_List('urls.txt')
    print(urls)
    _urls = dict(urls=urls)

    return app.response_class(
        response=json.dumps(_urls),
        status=200,
        mimetype='application/json'
    )


if __name__ == "__main__":
    align.init()
    app.debug = True
    app.run(host='127.0.0.1', port=9444)
