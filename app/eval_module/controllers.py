# Import flask dependencies
import csv
import re
import shutil
from flask import Blueprint, request, render_template, \
    flash, redirect, url_for, abort, json, make_response, send_from_directory

from app.src.UTIL.crawler import Crawler as crawler_folha
from app.src.UTIL.crawler_bbc import Crawler as crawler_bbc

# Import password / encryption helper tools
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import check_password_hash

# Import the database object from the main app module
from app import db, login_manager, app, is_safe_url

# Import module forms
from app.eval_module.forms import LoginForm

# Import module models (i.e. User)
from app.eval_module.models import User, PredAlignment, EvalModel, Batch, get_all_batch, query_by_id, get_all_em

# Define the blueprint: 'auth', set its url prefix: app.url/auth
from app.src.UTIL.metrics import precision, p_r_f_metrics
from app.src.align.align_tool import AlignTool
from config import STATIC_REL, BASE_DIR

mod_eval = Blueprint('eval', __name__, url_prefix='/eval')


# User loader for login_required decorator
@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    if request.path != url_for('eval.logout'):
        return redirect('%s?next=%s' % (url_for('eval.signin'), request.path))
    else:
        return redirect(url_for('eval.signin'))


@mod_eval.route('/signout/', methods=["GET"])
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for("eval.signin"))


# Set the route and accepted methods
@mod_eval.route('/login', methods=['GET', 'POST'])
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

    return render_template("eval_module/signin.html", form=form)


@mod_eval.route('/', methods=['GET'])
@login_required
def index():
    return render_template("eval_module/index.html")


@mod_eval.route('/submit', methods=["GET"])
@login_required
def submit():
    return render_template("eval_module/submit.html")


@mod_eval.route('/eval', methods=["GET"])
@login_required
def evaluation():
    return render_template(
        "eval_module/eval.html",
        batch_list=get_all_batch()  # get_all_batch()
    )


@mod_eval.route('/align_batch', methods=["GET", "POST"])
@login_required
def align_batch():
    links = list(set(request.form["batch_links"].split("\n")))
    name = request.form["batch_name"]
    increment = 1
    size = len(links)
    response = {}
    em_list = []
    for _link in links:
        if "http" in _link:
            # try:
            print("[ALIGN-BATCH | %r] Link %d of %d" % (name, increment, size))
            _experimento_pessoa = 2
            _experimento_objeto = 1

            if "folha" in _link:
                alinhador = AlignTool(crawler=crawler_folha)
            elif "bbc" in _link:
                alinhador = AlignTool(crawler=crawler_bbc)
            else:  # invalid url format
                return app.response_class(
                    response=json.dumps({'message': 'Bad request'}),
                    status=400,
                    mimetype='application/json'
                )

            result_pessoas, result_objetos, img_url, titulo, legenda, texto, dic_avaliacao, group = alinhador.align_from_url(
                _link, _experimento_pessoa, _experimento_objeto)

            if img_url != '':
                shutil.copy2(STATIC_REL + 'alinhamento2.jpg', img_url)

            # save all alignments to app.db
            group.add_db_all_alignments()
            pa_list = []
            for alignment in group.list_alignments:
                alignment.add_to_db()
                _aem = PredAlignment(label=alignment.term, alignment=alignment)
                pa_list.append(_aem)

            em = EvalModel(image=img_url, link=_link, text=texto, title=titulo, subtitle=legenda)
            em.add_aems(pa_list)
            em_list.append(em)
            response[str(increment)] = {"eval": dic_avaliacao, "img_url": img_url}
            increment += 1
            # except Exception as e:
            #     print("[ALIGN-BATCH | %r] Exception at link %d of %d:" % (name, increment, size))
            #     print(str(e))
            #     return app.response_class(
            #         response=json.dumps({'message': str(e)}),
            #         status=600,
            #         mimetype='application/json'
            #     )
    batch = Batch(name=name)
    batch.add_em(ems=em_list)
    batch.save()
    print("[ALIGN-BATCH | %r] SUCCESS!" % name)
    return app.response_class(
        response=json.dumps(response),
        status=200,
        mimetype="application/json",
        direct_passthrough=True
    )


@mod_eval.route('/eval_batch', methods=["POST"])
@login_required
def eval_batch():
    type_pattern = r"([a-z]*)_"
    radio_pattern = r"^(\w*)(_b)(\d*)(_e)(\d*)(_a)(\d*)"
    select_pattern = r"([a-z]*)_([a-z]*)_(\d*)"
    batch_id = -1
    em_id = -1
    for tag_id, value in request.form.items():
        str_match = [t(s) for t, s in zip((str,), re.search(type_pattern, tag_id).groups())][0]
        if str_match == "radio":
            (_, _, _batch_id, _, _em_id, _, _aem_id) = [
                t(s) for t, s in zip((str, str, int, str, int, str, int), re.search(radio_pattern, tag_id).groups())
            ]
            if batch_id == -1:
                batch_id = _batch_id
            if em_id == -1:
                em_id = _em_id

            try:
                aem = query_by_id(PredAlignment, _aem_id)
                aem.approval = value == "True"
                aem.add_self()
            except Exception as e:
                return app.response_class(
                    response=json.dumps({"error": str(e)}),
                    status=601,
                    mimetype="application/json"
                )
        elif str_match == "select":
            (_, _type_select, _aem_id) = [
                t(s) for t, s in zip((str, str, int), re.search(select_pattern, tag_id).groups())
            ]
            aem = query_by_id(PredAlignment, _aem_id)
            if _type_select == "mwe":
                aem.mwe_contrib = value
            elif _type_select == "syn":
                aem.syn_contrib = value
            aem.add_self()

    try:
        em = query_by_id(EvalModel, em_id)
        batch = query_by_id(Batch, batch_id)
        em.add_self()
        batch.save()
    except Exception as e:
        return app.response_class(
            response=json.dumps({"error": str(e)}),
            status=602,
            mimetype="application/json"
        )

    return app.response_class(
        response=json.dumps(request.form),
        status=200,
        mimetype="application/json",
        direct_passthrough=True
    )


@mod_eval.route("/view", methods=["GET"])
@login_required
def view():
    return render_template("eval_module/view.html", em_list=get_all_em())


def _download_csv(eval_list):
    with open(file=STATIC_REL + 'avaliacao.csv', encoding='utf-8', mode='w+') as csv_file:
        fields = ['Link', 'Termo', 'MWEs', 'Sinônimos', 'Aprovação', 'Ajuda_MWEs', 'Ajuda_Sinonimos']
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for eval in eval_list:
            if eval.alignments:
                for alignment in eval.alignments:
                    writer.writerow({
                        "Link": eval.link,
                        "Termo": alignment.label,
                        "MWEs": ', '.join(str(m) for m in alignment.alignment.mwes_model) if alignment.alignment.mwes_model else "-",
                        "Sinônimos": ', '.join(str(s) for s in alignment.alignment.syns_model) if alignment.alignment.syns_model else "-",
                        "Aprovação": alignment.approval,
                        "Ajuda_MWEs": alignment.mwe_contrib if alignment.alignment.mwes_model else "-",
                        "Ajuda_Sinonimos": alignment.syn_contrib
                    })
            else:
                writer.writerow({
                    "Link": eval.link,
                    "Termo": "-",
                    "MWEs": "-",
                    "Sinônimos": "-",
                    "Aprovação": "-",
                    "Ajuda_MWEs": "-",
                    "Ajuda_Sinonimos": "-"
                })
    return send_from_directory(BASE_DIR + "/" + STATIC_REL, 'avaliacao.csv', as_attachment=True)
    # return app.response_class(
    #     response=csv_file.read(),
    #     mimetype="text/csv",
    #     headers={"Content-disposition": "attachment; filename=avaliacao.csv"}
    # )


def _download_metrics(eval_list):
    with open(file=STATIC_REL + 'metrics.csv', encoding='utf-8', mode='w+') as metrics_file:
        writer = csv.DictWriter(metrics_file, fieldnames=['Medida', 'Medição'])
        writer.writeheader()
        correct = 0
        incorrect = 0
        non_aligned = 0
        aligned = 0
        for e in eval_list:
            if e.alignments:
                aligned += len(e.alignments)
                for a in e.alignments:
                    if a.approval:
                        correct += 1
                    else:
                        incorrect += 1
            else:
                non_aligned += 1

        p, r, f = p_r_f_metrics(correct=correct, incorrect=incorrect, total=aligned + non_aligned, as_percent=True)
        writer.writerow({'Medida': 'TOTAL DE ALINHAMENTOS', 'Medição': str(aligned)})
        writer.writerow({'Medida': 'NÃO ALINHADOS', 'Medição': str(non_aligned)})
        writer.writerow({'Medida': 'ALINHAMENTOS CORRETOS', 'Medição': str(correct)})
        writer.writerow({'Medida': 'ALINHAMENTOS INCORRETOS', 'Medição': str(incorrect)})

        writer.writerow({'Medida': 'PRECISAO', 'Medição': str(p)})
        writer.writerow({'Medida': 'COBERTURA', 'Medição': str(r)})
        writer.writerow({'Medida': 'MEDIDA-F', 'Medição': str(f)})
    return send_from_directory(BASE_DIR + "/" + STATIC_REL, 'metrics.csv', as_attachment=True)


@mod_eval.route('/export_eval', methods=["POST"])
@login_required
def export_eval():
    print("dentro de do_action")
    pattern = r"(\w*)_e(\d*)"
    eval_list = []
    for key, _ in request.form.items():
        if key != "select-actions" and key != "csrf_token":
            (input_type, id) = [t(s) for t, s in zip((str, int), re.search(pattern, key).groups())]
            if input_type == "checkbox":
                eval_list.append(EvalModel.query.get(id))
    if request.form['select-actions'] == "csv":
        return _download_csv(eval_list)
    elif request.form['select-actions'] == "mtr":
        return _download_metrics(eval_list)
    return app.response_class(
        response=json.dumps({}),
        mimetype="application/json",
        status=200,
        direct_passthrough=True
    )
