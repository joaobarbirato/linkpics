# Statement for enabling the development environment
DEBUG = True

# Define the application directory
import os
from secrets import token_urlsafe

# Thresholds
WUP_THR = 0.82
WUP_SYN_THR = 0.63

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = 'app/src/'
STATIC_REL = 'app/static/'
CORENLP_DIR = 'app/src/stanford-corenlp-full-2018-10-05'
TMP_DIR = BASE_DIR + '/app/tmp'

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

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = token_urlsafe(16)

# Secret key for signing cookies
SECRET_KEY = os.urandom(12)
