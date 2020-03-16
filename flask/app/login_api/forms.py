# Import Form and RecaptchaField (optional)
from flask import url_for
from flask_wtf import FlaskForm, Form  # , RecaptchaField

# Import Form elements such as TextField and BooleanField (optional)
from werkzeug.utils import redirect
from wtforms import PasswordField, StringField, HiddenField  # BooleanField

# Import Form validators
from wtforms.validators import Email, EqualTo, DataRequired, Length


# Define the login form (WTForms)
from app import get_redirect_target, is_safe_url


class RedirectForm(FlaskForm):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))


class LoginForm(RedirectForm):
    email = StringField('Email Address', [Email(),
                                          DataRequired(message='Forgot your email address?')])
    password = PasswordField('Password', [
        DataRequired(message='Must provide a password. ;-)'), Length(min=1, max=192)])
