import shutil

from flask import Blueprint, render_template, request, json

from app import app
from app.align_module.models import News, AlignmentGroup
from app.model_utils import PrintException
from app.src.align.align_tool import AlignTool
from app.src.idg.idgen import Generator
from config import STATIC_REL
from app.src.util.crawlers.crawler import Crawler as crawler_folha
from app.src.util.crawlers.crawler_bbc import Crawler as crawler_bbc

mod_desc = Blueprint('desc', __name__, url_prefix='/desc')


def do_describe(link, method):
    _link = link

    _experimento_pessoa = 2
    _experimento_objeto = 1
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
    news_object: News
    grupo: AlignmentGroup
    result_pessoas, result_objetos, img_url, titulo, legenda, texto, dic_avaliacao, grupo, news_object = alinhador.align_from_url(
        _link, _experimento_pessoa, _experimento_objeto)

    generator = Generator(news_object=news_object)
    generator.relate_amr()
    generator.generate(method=method)
    print(f'Generated:\n\t{generator.get_generated_descriptions()}')

    if img_url != '':
        shutil.copy2(STATIC_REL + 'alinhamento2.jpg', img_url)

    response = dict(result_pessoas=result_pessoas,
                    result_objetos=result_objetos,
                    img_alinhamento=img_url.replace(STATIC_REL, 'static/'),
                    texto=texto,
                    legenda=legenda,
                    titulo=titulo,
                    grupo=grupo,
                    message='',
                    news=news_object,
                    dic_avaliacao=dic_avaliacao)

    print(response)
    print(grupo.get_list_terms())
    return response


@mod_desc.route('/', methods=['GET', 'POST'])
def home():
    return render_template('desc_module/index.html', button="Gerar Descrições", form_action='/desc/geracao')


@mod_desc.route('/geracao', methods=['POST'])
def describe():
    try:
        response = do_describe(request.form["link"], method='baseline4')
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json',
            direct_passthrough=True
        )
    except Exception as exc:
        PrintException()
        return app.response_class(
            response=json.dumps({'error': 'erro'}),
            status =530,
            mimetype='application/json',
            direct_passthrough=True
        )
