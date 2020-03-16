from werkzeug.security import generate_password_hash

from app import db
from app.model_utils import Base


class User(Base):
    __tablename__ = 'eval_user'

    # User Name
    name = db.Column(db.String(128), nullable=False)

    # Identification Data: email & password
    email = db.Column(db.String(128), nullable=False,
                      unique=True)
    password_hash = db.Column(db.String(255, convert_unicode=True), nullable=False)

    # Authorisation Data: role
    role = db.Column(db.SmallInteger, nullable=False)
    authenticated = db.Column(db.Boolean, default=False)

    # New instance instantiation procedure
    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.role = role

    # Flask-login required methods
    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def __repr__(self):
        return '<User %r>' % self.name