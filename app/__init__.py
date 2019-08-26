# Import flask and template operators
from flask import Flask, render_template, request, json

# Import SQLAlchemy
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Define the WSGI application object
from urllib.parse import urlparse, urljoin
from werkzeug.exceptions import BadRequestKeyError

from app.src.UTIL import utils
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# Configurations
app.config.from_object('config')
csrf = CSRFProtect(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "eval.signin"

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)


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


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


# Import a module / component using its blueprint handler variable (mod_auth)
from app.eval_module.controllers import mod_eval as auth_module
from app.align_module.controllers import mod_align as align_module
from app.amr_module.controllers import mod_amr as amr_module
from app.desc_module.controllers import mod_desc as desc_module

# Register blueprint(s)
app.register_blueprint(auth_module)
app.register_blueprint(align_module)
app.register_blueprint(amr_module)
app.register_blueprint(desc_module)

# Build the database:
# This will create the database file using SQLAlchemy
db.create_all()


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
