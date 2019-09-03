import json
from flask import Blueprint, render_template, request
from flask_login import login_required

from app import app
from app.src.UTIL.amrtools.amr_networkx import crawl_link_to_generated_amr

mod_amr = Blueprint('amr', __name__, url_prefix='/amr')


@mod_amr.route('/', methods=['GET', 'POST'])
def home():
    return render_template('amr_module/index.html', button="Gerar AMRs")


@mod_amr.route('/generate', methods=['GET', 'POST'])
def generate():
    _link = request.form['link']
    dict_return = crawl_link_to_generated_amr(_link)

    return app.response_class(
        response=json.dumps(dict_return),
        status=200,
        mimetype='application/json'
    )
