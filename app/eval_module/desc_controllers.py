import csv
import re
from typing import Optional, Any

from flask import render_template, request, json, Blueprint, send_from_directory
from flask_login import login_required

from app import app
from app.align_module.models import News, Alignment
from app.desc_module.controllers import do_describe
from app.desc_module.models import Description
from app.eval_module.desc_models import create_desc_batch, create_desc_eval, get_all_batch_desc, DescEval, DescBatch
from app.eval_module.models import query_by_id
from app.model_utils import PrintException, _commit_session
from config import TMP_DIR, STATIC_REL, BASE_DIR

mod_eval_desc = Blueprint('eval_desc', __name__, url_prefix='/eval/desc')

FIELDS = ['Title', 'Link', 'Alignment', 'Description', 'AMR', 'Base', 'Others']


@mod_eval_desc.route('/view', methods=["GET", "POST"])
def view_desc():
    return render_template("desc_module/view.html", batch_list=get_all_batch_desc())


@mod_eval_desc.route('/submit', methods=["GET", "POST"])
def submit_desc():
    return render_template(
        "desc_module/submit.html"
    )


@mod_eval_desc.route('/eval')
# @login_required
def evaluation_desc():
    return render_template(
        "desc_module/eval.html",
        batch_list=get_all_batch_desc()
    )


@mod_eval_desc.route('/describe_batch', methods=["GET", "POST"])
def describe_batch():
    try:
        links = list(set(request.form["batch_links"].split("\n")))
        links.sort()
        total = len(links)
        batch_name = request.form["batch_name"]
        restriction = request.form["restriction"]
        method = request.form["method"]
        failed = []
        with open(f'{TMP_DIR}/test_description.csv', 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
            writer.writeheader()

        desc_batch = create_desc_batch(name=f'{batch_name}_method_{method}')

        for i, link in enumerate(links):
            try:
                print(f"#####\n\t[{i + 1}/{total}]\n#####")
                link = link.replace('\r', '')
                response = do_describe(link=link, method=method)
                news_object = response["news"]
                grupo = response["grupo"]
                for alignment in grupo.get_all_alignments():
                    if restriction == "all" or \
                            (restriction == "ne" and alignment.get_is_ne()) or \
                            (restriction == "obj" and not alignment.get_is_ne()):
                        alignment.add_to_db()
                        desc = alignment.get_description()
                        if desc is not None:
                            desc_eval = create_desc_eval(desc_model=desc)
                            desc_batch.add_desc_eval(desc_eval)
                            desc_eval.add_self()
                            desc_batch.add_self()
                news_object.set_path(response["img_alinhamento"])
                news_object.save()
                _write_test_csv(news_object)
                _commit_session()
            except Exception as exc:
                PrintException()
                failed.append((link, f'{str(exc)}'))

        if failed:
            with open(f'{TMP_DIR}/failed_links.txt', 'w') as link_file:
                for link, exc in failed:
                    link_file.write(f'{link}, {exc}\n')

        from app.align_module.models import News
        print("Done!")
        return app.response_class(
            response=json.dumps({"success": "success"}),
            status=200,
            mimetype="application/json",
            direct_passthrough=True
        )
    except Exception as exc:
        PrintException()
        return app.response_class(
            response=json.dumps({"error": "error"}),
            status=200,
            mimetype="application/json",
            direct_passthrough=True
        )


def _write_test_csv(news):
    with open(f'{TMP_DIR}/test_description.csv', 'a') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        news: News
        title = news.get_sentences()[0]
        link = news.get_link()
        alignment: Alignment
        for alignment in news.alignments():
            desc: Description = alignment.get_description()
            writer.writerow({
                'Title': title,
                'Link': link,
                'Alignment': alignment.get_term(),
                'Description': desc if desc is not None else '',
                'AMR': desc.get_amr() if desc is not None else '',
                'Base': desc.get_main().get_penman(return_type='str') if desc is not None else '',
                'Others': "\n".join([amr.get_penman(return_type='str') for amr in desc.get_adjacents()]) if desc is not None else ''
            })


@mod_eval_desc.route('/eval_batch', methods=["POST"])
# @login_required
def eval_desc_batch():
    type_pattern = r"([a-z]*)_"
    radio_pattern = r"^(\w*)(_b)(\d*)(_e)(\d*)"
    print([item for item in request.form.items()])
    batch_id = -1
    for tag_id, value in request.form.items():
        str_match = [t(s) for t, s in zip((str,), re.search(type_pattern, tag_id).groups())][0]
        if str_match == "radio":
            (_, _, batch_id, _, de_id) = [
                t(s) for t, s in zip((str, str, int, str, int), re.search(radio_pattern, tag_id).groups())
            ]
            try:
                de: DescEval = query_by_id(DescEval, de_id)
                de.approve(value=value)
                de.add_self()

            except Exception as e:
                PrintException()
                return app.response_class(
                    response=json.dumps({"error": str(e)}),
                    status=601,
                    mimetype="application/json"
                )
    try:
        _commit_session()
    except Exception as exc:
        PrintException()
        return app.response_class(
            response=json.dumps({"error": str(e)}),
            status=621,
            mimetype="application/json"
        )
    return app.response_class(
        response=json.dumps(request.form),
        status=200,
        mimetype="application/json"
    )


def _download_csv(eval_list):
    file_name = 'avaliacao_desc.csv'
    with open(file=STATIC_REL + file_name, encoding='utf-8', mode='w+') as csv_file:
        fields = FIELDS
        fields.append('Approval')
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()

        eval: DescEval
        for eval in eval_list:
            writer.writerow({
                'Title': eval.get_news().get_title(),
                'Link': eval.get_news().get_link(),
                'Alignment': eval.get_desc().get_alignment(),
                'Description': eval.get_desc(),
                'AMR': eval.get_desc().get_amr(),
                'Base': eval.get_desc().get_main().get_penman(return_type='str'),
                'Others': "\n".join(
                    [amr.get_penman(return_type='str') for amr in eval.get_desc().get_adjacents()]),
                'Approval': eval.get_approval_string(),
            })

    return send_from_directory(BASE_DIR + "/" + STATIC_REL, file_name, as_attachment=True)


def _download_metrics(eval_list):
    file_name = 'metrics_desc.csv'
    with open(file=STATIC_REL + file_name, encoding='utf-8', mode='w+') as metrics_file:
        writer = csv.DictWriter(metrics_file, fieldnames=['Medida', 'Medição'])
        writer.writeheader()
        correct = 0
        p_correct = 0
        incorrect = 0
        invalid = 0

        e: DescEval
        for e in eval_list:
            if e.approval == 2:
                correct += 1
            elif e.approval == 1:
                p_correct += 1
            elif e.approval == 0:
                incorrect += 1
            elif e.approval == -1:
                invalid += 1

        writer.writerow({'Medida': 'TOTAL DE DESCRIÇÕES', 'Medição': str(len(eval_list))})
        writer.writerow({'Medida': 'CORRETAS', 'Medição': str(correct)})
        writer.writerow({'Medida': 'PARCIALMENTE CORRETAS', 'Medição': str(p_correct)})
        writer.writerow({'Medida': 'INCORRETAS', 'Medição': str(incorrect)})
        writer.writerow({'Medida': 'INVÁLIDAS', 'Medição': str(invalid)})

    return send_from_directory(BASE_DIR + "/" + STATIC_REL, file_name, as_attachment=True)


@mod_eval_desc.route('/export_eval', methods=["POST"])
def export_eval():
    pattern = r"(\w*)_e(\d*)"
    eval_list = []
    for key, _ in request.form.items():
        if key != "select-actions" and key != "csrf_token":
            (input_type, id) = [t(s) for t, s in zip((str, int), re.search(pattern, key).groups())]
            if input_type == "checkbox":
                eval_list.append(DescEval.query.get(id))
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
