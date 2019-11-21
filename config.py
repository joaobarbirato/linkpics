# Thresholds
import os

DEBUG=True

WUP_THR = 0.82
WUP_SYN_THR = 0.63

HOST='127.0.0.1'
PORT=9444

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = 'back_app/src/'
STATIC_REL = 'back_app/static/'
BACKUP_DIR = BASE_DIR + '/back_app/noticias_backup'

# Define the database - we are working with
# SQLite for this example
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True
DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2