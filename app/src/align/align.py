import shutil

from flask import json

from app import app
from app.align_module.models import News, AlignmentGroup
from app.model_utils import PrintException
from app.src.align.align_tool import AlignTool
from app.src.util import Crawler as crawler_folha
from app.src.util.crawlers.crawler_bbc import Crawler as crawler_bbc
from config import STATIC_REL


def do_align(link):
    try:
        _experimento_pessoa = 2
        _experimento_objeto = 1
        if "folha" in link:
            alinhador = AlignTool(crawler=crawler_folha)
        elif "bbc" in link:
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
        try:
            result_pessoas, result_objetos, img_url, titulo, legenda, texto, dic_avaliacao, grupo, news_object = \
                alinhador.align_from_url(link, _experimento_pessoa, _experimento_objeto)
        except Exception as exc:
            result_pessoas, result_objetos, img_url, titulo, legenda, texto, dic_avaliacao, grupo, news_object = \
                alinhador.align_backup(link, _experimento_pessoa, _experimento_objeto)

        if img_url != '':
            shutil.copy2(STATIC_REL + 'alinhamento2.jpg', img_url)

        return dict(result_pessoas=result_pessoas,
                    result_objetos=result_objetos,
                    img_alinhamento=img_url.replace(STATIC_REL, 'static/'),
                    texto=texto,
                    legenda=legenda,
                    titulo=titulo,
                    grupo=grupo,
                    news=news_object,
                    dic_avaliacao=dic_avaliacao)
    except Exception as exc:
        PrintException()
