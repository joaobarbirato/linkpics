from flask import Blueprint, render_template, request, json
from flask_login import login_required

from app import app
from app.src.align.align import do_align

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


@mod_align.route('/alinhamento', methods=['POST'])
def alinhar():
    try:
        _link = request.form['link']
        response = do_align(link=_link)
        print(response)
        print(response['grupo'].get_list_terms())
        response.pop('news', None)
        response.pop('grupo', None)
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



