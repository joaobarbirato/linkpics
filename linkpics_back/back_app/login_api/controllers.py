from flask import request, url_for, redirect, flash, abort, render_template, Blueprint
# from flask_login import current_user, logout_user, login_manager
from werkzeug.security import check_password_hash

from back_app import is_safe_url, db, login_manager

from flask_login import login_user, login_required, current_user, logout_user

# Import module forms
from back_app.login_api.forms import LoginForm
from back_app.login_api.models import User


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    if request.path != url_for('eval.logout'):
        return redirect('%s?next=%s' % (url_for('eval.signin'), request.path))
    else:
        return redirect(url_for('eval.signin'))


mod_login = Blueprint('login', __name__, url_prefix='/login')


@mod_login.route('/signout/', methods=["GET"])
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for("eval.signin"))


@mod_login.route('/signin/', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('eval.index'))

    # If sign in form is submitted
    form = LoginForm(request.form)

    # Verify the sign in form
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash('Welcome %s' % user.name)
            _next = request.args.get('next')
            if not is_safe_url(_next):
                return abort(400)

            return form.redirect('eval.index')

        flash('Wrong email or password', 'error-message')

    return render_template("eval_api/signin.html", form=form)