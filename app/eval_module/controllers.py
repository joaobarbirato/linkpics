# Import flask dependencies
import csv
import re
import shutil
from flask import Blueprint, request, render_template, \
    flash, redirect, url_for, abort, json, send_from_directory

from app.align_module.base_model import MWE, Synonym
from app.src.util.crawlers.crawler import Crawler as crawler_folha
from app.src.util.crawlers.crawler_bbc import Crawler as crawler_bbc

# Import password / encryption helper tools
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import check_password_hash

# Import the database object from the main app module
from app import db, login_manager, app, is_safe_url

# Import module forms
from app.eval_module.forms import LoginForm

# Import module models (i.e. User)
from app.eval_module.models import User, PredAlignment, EvalModel, Batch, get_all_batch, query_by_id

# Define the blueprint: 'auth', set its url prefix: app.url/auth
from app.src.util.metrics import p_r_f_metrics
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
    restriction = request.form["restriction"]
    increment = 1
    size = len(links)
    response = {}
    em_list = []
    print("links:", links)
    for _link in links:
        print("link antes do replace:", _link)
        _link = _link.replace("\r", "")
        print("new link:", _link)
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
            pa_list = []
            for alignment in group.list_alignments:
                if restriction == "all" or \
                        (restriction == "ne" and alignment.get_is_ne()) or \
                        (restriction == "obj" and not alignment.get_is_ne()):
                    alignment.add_to_db()
                    _aem = PredAlignment(label=alignment.term, alignment=alignment)
                    pa_list.append(_aem)

            em = EvalModel(image=img_url, link=_link, text=texto, title=titulo, subtitle=legenda, restrictions=restriction)
            if pa_list:
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
    # select_pattern = r"([a-z]*)_([a-z]*)_(\d*)"
    mwe_syn_pattern = r"[mwe|syn]_(\d*)"
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
        elif str_match == "mwe":
            mwe_id = [t(s) for t, s in zip((str, str, int), re.search(mwe_syn_pattern, tag_id).groups())]
            mwe = query_by_id(MWE, mwe_id)
            aem = mwe.get_parent()
            mwe.set_approval(appr= value == "True")
            mwe.add_self()
            aem.add_self()
            # (_, _type_select, _aem_id) = [
            #     t(s) for t, s in zip((str, str, int), re.search(select_pattern, tag_id).groups())
            # ]
            # aem = query_by_id(PredAlignment, _aem_id)
            # if _type_select == "mwe":
            #     aem.mwe_contrib = value
            # elif _type_select == "syn":
            #     aem.syn_contrib = value
            # aem.add_self()
        elif str_match == "syn":
            syn_id = [t(s) for t, s in zip((str, str, int), re.search(mwe_syn_pattern, tag_id).groups())]
            syn = query_by_id(Synonym, syn_id)
            aem = syn.get_parent()
            syn.set_approval(appr=value == "True")
            syn.add_self()
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
    return render_template("eval_module/view.html", batch_list=get_all_batch())


def _download_csv(eval_list):
    with open(file=STATIC_REL + 'avaliacao.csv', encoding='utf-8', mode='w+') as csv_file:
        fields = ['EvalID', 'Link', 'AlgID', 'Termo', 'Aprovação', 'MWEs', 'Aprovação_MWEs', 'Sinônimos', 'Aprovação_Sinonimos']
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for eval in eval_list:
            if eval.alignments:
                for alignment in eval.alignments:
                    writer.writerow({
                        "EvalID": eval.id,
                        "Link": eval.link,
                        "AlgID": alignment.id,
                        "Termo": alignment.label,
                        "Aprovação": alignment.approval,
                        "MWEs": ', '.join(str(m) for m in alignment.alignment.mwes_model) if alignment.alignment.mwes_model else "-",
                        "Aprovação_MWEs": ', '.join(str(m.approval) for m in alignment.alignment.mwes_model) if alignment.alignment.mwes_model else "-",
                        "Sinônimos": ', '.join(str(s) for s in alignment.alignment.syns_model) if alignment.alignment.syns_model else "-",
                        "Aprovação_Sinonimos": ', '.join(str(s.approval) for s in alignment.alignment.syns_model) if alignment.alignment.syns_model else "-",
                    })
            else:
                writer.writerow({
                    "EvalID": eval.id,
                    "Link": eval.link,
                    "AlgID": "-",
                    "Termo": "-",
                    "Aprovação": "-",
                    "MWEs": "-",
                    "Aprovação_MWEs": "-",
                    "Sinônimos": "-",
                    "Aprovação_Sinonimos": "-"
                })
    return send_from_directory(BASE_DIR + "/" + STATIC_REL, 'avaliacao.csv', as_attachment=True)


def _download_metrics(eval_list):
    with open(file=STATIC_REL + 'metrics.csv', encoding='utf-8', mode='w+') as metrics_file:
        writer = csv.DictWriter(metrics_file, fieldnames=['Medida', 'Medição'])
        writer.writeheader()
        correct = 0
        incorrect = 0
        aligned = 0
        someone_has_mwe = False
        someone_has_syn = False

        correct_mwe = 0
        incorrect_mwe = 0

        correct_syn = 0
        incorrect_syn = 0

        for e in eval_list:
            if e.alignments:
                aligned += len(e.alignments)
                for pa in e.alignments:
                    if not someone_has_mwe and pa.alignment.get_has_mwes_model():
                        someone_has_mwe = True
                    if not someone_has_syn and pa.alignment.get_has_syns_model():
                        someone_has_syn = True

                    if pa.alignment.get_has_mwes_model():
                        for mwe in pa.alignment.mwes_model:
                            if mwe.approval:
                                correct_mwe += 1
                            else:
                                incorrect_mwe += 1

                    if pa.alignment.get_has_syns_model():
                        for syn in pa.alignment.syns_model:
                            if syn.approval:
                                correct_syn += 1
                            else:
                                incorrect_syn += 1

                    if pa.approval:
                        correct += 1
                    else:
                        incorrect += 1

        p, r, f = p_r_f_metrics(correct=correct, incorrect=incorrect, total=aligned, as_percent=True)
        writer.writerow({'Medida': 'TOTAL DE NOTÍCIAS', 'Medição': str(len(eval_list))})
        writer.writerow({'Medida': 'TOTAL DE ALINHAMENTOS', 'Medição': str(aligned)})
        writer.writerow({'Medida': 'ALINHAMENTOS CORRETOS', 'Medição': str(correct)})
        writer.writerow({'Medida': 'ALINHAMENTOS INCORRETOS', 'Medição': str(incorrect)})

        writer.writerow({'Medida': 'PRECISAO_GERAL', 'Medição': str(p) + "%"})
        writer.writerow({'Medida': 'COBERTURA_GERAL', 'Medição': str(r) + "%"})
        writer.writerow({'Medida': 'MEDIDA-F_GERAL', 'Medição': str(f) + "%"})

        if someone_has_mwe:
            writer.writerow({'Medida': '', 'Medição': ''})
            p_mwe, r_mwe, f_mwe = p_r_f_metrics(correct=correct_mwe, incorrect=incorrect_mwe, total=correct_mwe+incorrect_mwe, as_percent=True)
            writer.writerow({'Medida': 'TOTAL DE COMPOSTOS', 'Medição': str(correct_mwe + incorrect_mwe)})
            writer.writerow({'Medida': 'COMPOSTOS CORRETOS', 'Medição': str(correct_mwe)})
            writer.writerow({'Medida': 'COMPOSTOS INCORRETOS', 'Medição': str(incorrect_mwe)})
            writer.writerow({'Medida': 'PRECISAO_MWE', 'Medição': str(p_mwe) + "%"})
            writer.writerow({'Medida': 'COBERTURA_MWE', 'Medição': str(r_mwe) + "%"})
            writer.writerow({'Medida': 'MEDIDA-F_MWE', 'Medição': str(f_mwe) + "%"})

        if someone_has_syn:
            writer.writerow({'Medida': '', 'Medição': ''})
            p_syn, r_syn, f_syn = p_r_f_metrics(correct=correct_syn, incorrect=incorrect_syn, total=correct_syn+incorrect_syn, as_percent=True)
            writer.writerow({'Medida': 'TOTAL DE SINÔNIMOS', 'Medição': str(correct_syn + incorrect_syn)})
            writer.writerow({'Medida': 'SINÔNIMOS CORRETOS', 'Medição': str(correct_syn)})
            writer.writerow({'Medida': 'SINÔNIMOS INCORRETOS', 'Medição': str(incorrect_syn)})
            writer.writerow({'Medida': 'PRECISAO_SIN', 'Medição': str(p_syn)})
            writer.writerow({'Medida': 'COBERTURA_SIN', 'Medição': str(r_syn)})
            writer.writerow({'Medida': 'MEDIDA-F_SIN', 'Medição': str(f_syn)})

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
