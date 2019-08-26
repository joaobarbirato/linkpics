from flask import Blueprint, render_template

mod_desc = Blueprint('desc', __name__, url_prefix='/desc')


@mod_desc.route('/', methods=['GET', 'POST'])
def home():
    return render_template('desc_module/index.html', button="Gerar Descrições")
