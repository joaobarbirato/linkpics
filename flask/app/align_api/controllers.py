import shutil

from flask import Blueprint, request, json

from app import app
from app.src.align.align_tool import AlignTool
from app.crawlers.crawler import Crawler as crawler_folha
from app.crawlers.crawler_bbc import Crawler as crawler_bbc
from config import STATIC_REL, HOST, PORT

mod_align = Blueprint('align', __name__, url_prefix='/align')


def do_alignment(link, restriction=None):
    _experimento_pessoa = 2
    _experimento_objeto = 1
    if "folha" in link:
        alinhador = AlignTool(crawler=crawler_folha, restriction=restriction)
    elif "bbc" in link:
        alinhador = AlignTool(crawler=crawler_bbc, restriction=restriction)
    else:  # invalid url format
        return app.response_class(
            response=json.dumps({'message': 'Bad request'}),
            status=400,
            mimetype='application/json'
        )
    try:
        news_object = alinhador.align_from_url(
            link, _experimento_pessoa, _experimento_objeto)
    except:
        news_object = alinhador.align_backup(
            link, _experimento_pessoa, _experimento_objeto)

    if news_object.link_img != '':
        shutil.copy2(STATIC_REL + 'alinhamento2.jpg', news_object.link_img)

    response = dict(img_alinhamento=f"http://{HOST}:{PORT}/{news_object.link_img.replace(STATIC_REL, 'static/')}",
                    texto=news_object.marked_text,
                    legenda=news_object.marked_subtitle,
                    titulo=news_object.marked_title,
                    full_json=news_object.serialize)

    print(response)
    print(news_object.alignments)
    return response


@mod_align.route('/all_json', methods=['POST'])
def all_json():
    link_list = list(set(request.args.get('linklist').split(',')))
    restriction = request.args.get('restriction')
    news_dict = {}
    list_size = len(link_list)
    for i, link in enumerate(link_list):
        treated_link = link.replace('\r', '')
        print(f'Completed: {str(i)}/{str(list_size)}')
        dict_response = do_alignment(treated_link, restriction)
        news_dict[f'news#{str(i)}'] = dict_response['full_json']

    print(f'Completed: {str(list_size)}/{str(list_size)}')

    return app.response_class(
        response=json.dumps(news_dict),
        status=200,
        mimetype='application/json',
        direct_passthrough=True
    )


@mod_align.route('/', methods=['POST'])
# @login_required
def alinhar():
    # try:
    link = request.args.get('link')
    print(request.args)
    response = do_alignment(link)
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
