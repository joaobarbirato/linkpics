from urllib.parse import urlparse, urljoin

from flask import Flask, render_template, request, json
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequestKeyError

from back_app.src.UTIL import utils

app = Flask(__name__)
db = SQLAlchemy(app)
# Define the database object which is imported
# by modules and controllers

app.config.from_object('config')

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "eval.signin"


# Sample HTTP error handling
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


from back_app.eval_api.controllers import mod_eval
from back_app.align_api.controllers import mod_align
from back_app.login_api.controllers import mod_login

app.register_blueprint(mod_align)
app.register_blueprint(mod_eval)
app.register_blueprint(mod_login)

db.create_all()

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# Global routes
@app.route('/upload', methods=['POST'])
def upload_link_files():
    try:
        file = request.files['choosed_file']
    except BadRequestKeyError as e:
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
