from flask import Flask

front_app = Flask(__name__)
front_app.config.from_object('config')


from front_app.main_module.controllers import mod_main


front_app.register_blueprint(mod_main)