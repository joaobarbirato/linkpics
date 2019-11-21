import json

from flask import Blueprint, render_template, request, app, session, send_from_directory, send_file, Response

from front_app import front_app
from front_app.utils.communication import request_to_back

from config import TMP_DIR

mod_main = Blueprint('main', __name__, url_prefix='/')


def render_index(action=None):
    return render_template('main_module/index.html', form_action=action, button="Alinhamento Texto Imagem")


@mod_main.route("/")
def home():
    return render_index(action='/alignment')


@mod_main.route('/alignment', methods=['POST'])
def align():
    link = request.form['link']
    response: Response = request_to_back(action='align', url=link)
    print(response.data)
    file_name = 'alignment-data.json'
    directory = f'{TMP_DIR}'
    data = json.loads(response.data.decode('utf-8'))['full_json']
    with open(f'{directory}/{file_name}', 'w') as json_file:
        json.dump(data, fp=json_file, indent='\t')
    return response


@mod_main.route('/submit_json', methods=["GET"])
def submit_json():
    return render_template('main_module/submit.html')


@mod_main.route('/all_json', methods=['POST'])
def all_json():
    links = list(set(request.form["links"].split("\n")))
    restriction = request.form["restriction"]
    response: Response = request_to_back(action='all_json', linklist=links, restriction=restriction)
    data = json.loads(response.data.decode('utf-8'))
    with open(f'{TMP_DIR}/bbc_alignments.json', 'w') as json_file:
        json.dump(data, fp=json_file, indent='\t')
    return response


@mod_main.route('/full_json', methods=['GET'])
def download_json():
    file_name = 'alignment-data.json'
    directory = f'{TMP_DIR}'
    return send_from_directory(directory=directory, filename=file_name, as_attachment=True)


@mod_main.route('/dictionary', methods=['GET'])
def download_dictionary():
    return send_from_directory(directory=TMP_DIR, filename='bbc_alignments.json', as_attawwchment=True)