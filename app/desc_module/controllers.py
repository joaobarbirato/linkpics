import csv
import shutil

from flask import Blueprint, render_template, request, json

from app import app
from app.align_module.models import News, Alignment, AlignmentGroup
from app.desc_module.models import Description
from app.model_utils import _add_session, _commit_session, PrintException
from app.src.align.align_tool import AlignTool
from app.src.idg.idgen import Generator
from config import STATIC_REL, TMP_DIR
from app.src.util.crawlers.crawler import Crawler as crawler_folha
from app.src.util.crawlers.crawler_bbc import Crawler as crawler_bbc

mod_desc = Blueprint('desc', __name__, url_prefix='/desc')

_FIELDS = ['Title', 'Link', 'Alignment', 'Description', 'AMR', 'Base', 'Others']


def _do_describe(link):
    try:
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
        generator.generate(method='baseline1')
        print(f'Generated:\n\t{generator.get_generated_descriptions()}')

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

        grupo.add_db_all_alignments()

        news_object.save()
        _write_test_csv(news_object)
        _commit_session()
        print(response)
        print(grupo.get_list_terms())
        return app.response_class(
            response=json.dumps(response),
            status=200,
            mimetype='application/json',
            direct_passthrough=True
        )
    except Exception as e:
        PrintException()
        return app.response_class(
            response=json.dumps({'message': f'{e}'}),
            status=600,
            mimetype='application/json'
        )


@mod_desc.route('/', methods=['GET', 'POST'])
def home():
    return render_template('desc_module/index.html', button="Gerar Descrições", form_action='/desc/geracao')


@mod_desc.route('/geracao', methods=['POST'])
def describe():
    response = _do_describe(request.form["link"])
    # _commit_session()
    return response


@mod_desc.route('/eval', methods=["GET", "POST"])
def eval_descriptions():
    return render_template(
        "desc_module/submit.html"
    )


@mod_desc.route('/describe_batch', methods=["GET", "POST"])
def describe_batch():
    try:
        links = list(set(request.form["batch_links"].split("\n")))
        links.sort()
        total = len(links)
        failed = []
        with open(f'{TMP_DIR}/test_description.csv', 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=_FIELDS)
            writer.writeheader()

        for i, link in enumerate(links):
            try:
                print(f"#####\n\t[{i + 1}/{total}]\n#####")
                link = link.replace('\r', '')
                _do_describe(link)
            except Exception as exc:
                PrintException()
                failed.append((link, f'{str(exc)}'))

        if failed:
            with open(f'{TMP_DIR}/failed_links.txt', 'w') as link_file:
                for link, exc in failed:
                    link_file.write(f'{link}, {exc}\n')

        from app.align_module.models import News
        print("Done!")
        return app.response_class(
            response=json.dumps({"success": "success"}),
            status=200,
            mimetype="application/json",
            direct_passthrough=True
        )
    except Exception as exc:
        PrintException()


# ['link', 'Title', 'Alignment', 'description']
def _write_test_csv(news):
    with open(f'{TMP_DIR}/test_description.csv', 'a') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=_FIELDS)
        news: News
        title = news.get_sentences()[0]
        link = news.get_link()
        alignment: Alignment
        for alignment in news.alignments():
            desc: Description = alignment.get_description()
            writer.writerow({
                'Title': title,
                'Link': link,
                'Alignment': alignment.get_term(),
                'Description': desc if desc is not None else '',
                'AMR': desc.get_amr() if desc is not None else '',
                'Base': desc.get_main().get_penman(return_type='str') if desc is not None else '',
                'Others': "\n".join([amr.get_penman(return_type='str') for amr in desc.get_adjacents()]) if desc is not None else ''
            })