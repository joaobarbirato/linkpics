from flask import Blueprint, render_template, request, json

from app import app
from app.model_utils import PrintException
from app.src.align.align import do_align
from app.src.idg.idgen import Generator

mod_desc = Blueprint('desc', __name__, url_prefix='/desc')


def do_describe(link, method, select=0):
    response = do_align(link=link)
    print(response)
    generator = Generator(news_object=response['news'])
    generator.relate_amr()
    generator.generate(method=method, select=select)
    print(f'Generated:\n\t{generator.get_generated_descriptions()}')
    print(response['grupo'].get_list_terms())
    return response


@mod_desc.route('/', methods=['GET', 'POST'])
def home():
    return render_template('desc_module/index.html', button="Gerar Descrições", form_action='/desc/geracao')


@mod_desc.route('/geracao', methods=['POST'])
def describe():
    try:
        response = do_describe(request.form["link"], method='baseline4')
        response.pop('news', None)
        response.pop('grupo', None)
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
            status=530,
            mimetype='application/json',
            direct_passthrough=True
        )
