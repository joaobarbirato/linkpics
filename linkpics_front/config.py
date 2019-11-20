import os

HOST='127.0.0.1'
PORT=9445

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

TMP_DIR = BASE_DIR + '/front_app/tmp'

DEBUG=True

SECRET_KEY = os.urandom(32)
