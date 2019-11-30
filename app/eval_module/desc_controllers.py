import codecs
import csv
import re
from typing import Optional, Any, Union

from flask import render_template, request, json, Blueprint, send_from_directory
from flask_login import login_required

from app import app
from app.align_module.models import News, Alignment, AlignmentGroup
from app.desc_module.controllers import do_describe
from app.desc_module.models import Description
from app.eval_module.desc_models import create_desc_batch, create_desc_eval, get_all_batch_desc, DescEval, DescBatch, \
    get_all_desc_eval
from app.eval_module.models import query_by_id
from app.model_utils import PrintException, _commit_session
from config import TMP_DIR, STATIC_REL, BASE_DIR

mod_eval_desc = Blueprint('eval_desc', __name__, url_prefix='/eval/desc')

FIELDS = ['Title', 'Link', 'Alignment', 'Description', 'AMR', 'Base', 'Others']


hcl = list(set(['http://www.bbc.com/future/story/20170818-voyager-inside-the-worlds-greatest-space-mission', 'http://www.bbc.com/news/blogs-trending-40271663', 'http://www.bbc.com/news/blogs-trending-31736316', 'http://www.bbc.com/news/blogs-trending-33224187', 'http://www.bbc.com/news/blogs-trending-35376072', 'http://www.bbc.co.uk/earth/story/20150430-the-orange-tips-search-for-a-mate', 'http://www.bbc.com/news/blogs-trending-38031629', 'http://www.bbc.com/autos/story/20161223-last-minute-gifts-for-green-minded-drivers', 'http://www.bbc.com/news/blogs-trending-39205935', 'http://www.bbc.com/future/story/20171027-the-stray-dogs-that-paved-the-way-to-the-stars', 'http://www.bbc.com/culture/story/20170428-how-one-creature-haunts-our-thoughts', 'http://www.bbc.com/news/blogs-trending-33066865', 'http://www.bbc.com/news/blogs-trending-37925961', 'http://www.bbc.com/news/blogs-trending-32481796', 'http://www.bbc.com/news/blogs-trending-39278010', 'http://www.bbc.com/news/blogs-trending-37222375', 'http://www.bbc.com/news/blogs-trending-39639834', 'http://www.bbc.com/autos/story/20161024-top-gear-drives-ferraris-spiky-spiteful-f12tdf', 'http://www.bbc.com/news/blogs-trending-38383126', 'http://www.bbc.com/news/blogs-trending-32340384', 'http://www.bbc.com/news/blogs-trending-36970535', 'http://www.bbc.com/earth/story/20170605-the-most-powerful-punches-and-kicks-of-all-time', 'http://www.bbc.com/news/blogs-trending-32417773', 'http://www.bbc.com/news/blogs-trending-40299919', 'http://www.bbc.com/future/story/20170517-the-strange-sheep-that-baffled-scientists', 'http://www.bbc.com/news/blogs-trending-38748621', 'http://www.bbc.com/news/blogs-trending-34879990', 'http://www.bbc.com/news/blogs-trending-37645992', 'http://www.bbc.com/earth/story/20170608-some-dung-beetles-have-taken-to-decapitating-millipedes', 'http://www.bbc.com/news/blogs-trending-38804499', 'http://www.bbc.com/news/blogs-trending-36985697', 'http://www.bbc.com/future/story/20170503-the-worlds-biggest-plane-may-have-a-new-mission', 'http://www.bbc.com/news/health-42009932', 'http://www.bbc.com/autos/story/20160719-hide-and-seek-on-the-us-mexico-line', 'http://www.bbc.com/news/blogs-trending-32971094', 'http://www.bbc.com/news/blogs-trending-40326003', 'http://www.bbc.com/news/blogs-trending-34967254', 'http://www.bbc.com/news/technology-38364076', 'http://www.bbc.com/news/blogs-trending-32529980', 'http://www.bbc.com/news/blogs-trending-37222517', 'http://www.bbc.com/news/blogs-trending-32723202', 'http://www.bbc.com/autos/story/20161206-driving-bentleys-bentayga-diesel', 'http://www.bbc.com/future/story/20170627-how-do-you-treat-a-dog-with-ocd', 'http://www.bbc.com/news/blogs-trending-33250663', 'http://www.bbc.com/news/technology-39803425', 'http://www.bbc.com/news/technology-15969065', 'http://www.bbc.com/news/blogs-trending-37197751', 'http://www.bbc.com/news/blogs-trending-36384312', 'http://www.bbc.com/future/story/20171027-the-magic-cakes-that-come-from-a-packet', 'http://www.bbc.com/earth/story/20141117-why-seals-have-sex-with-penguins', 'http://www.bbc.com/news/blogs-trending-40775490', 'http://www.bbc.com/news/blogs-trending-37179158', 'http://www.bbc.com/earth/story/20170608-pirate-spiders-make-a-living-by-preying-on-other-spiders', 'http://www.bbc.com/autos/story/20160927-flat-out-in-britains-fiercest-cat', 'http://www.bbc.com/culture/story/20170630-are-women-less-important-than-cows-in-india', 'http://www.bbc.com/news/blogs-trending-36499488', 'http://www.bbc.com/news/blogs-trending-32797265', 'http://www.bbc.com/news/blogs-trending-37679612', 'http://www.bbc.com/news/blogs-trending-32251712', 'http://www.bbc.com/culture/story/20170707-the-gorilla-that-loves-to-look-at-smartphones', 'http://www.bbc.com/future/story/20171025-what-if-the-vw-beetle-had-never-existed', 'http://www.bbc.com/future/story/20170404-the-british-airliner-that-changed-the-world', 'http://www.bbc.com/news/blogs-trending-39351853', 'http://www.bbc.com/autos/story/20160409-meet-darpas-long-range-autonomous-submarine-hunter', 'http://www.bbc.com/future/story/20170808-climate-change-is-disrupting-the-birds-and-the-bees', 'http://www.bbc.com/news/blogs-trending-35263200', 'http://www.bbc.com/news/blogs-trending-37752730', 'http://www.bbc.com/autos/story/20160824-how-to-roll-like-a-real-finn', 'http://www.bbc.com/news/blogs-trending-40340620', 'http://www.bbc.com/news/blogs-trending-40173553', 'http://www.bbc.com/news/blogs-trending-37233913', 'http://www.bbc.com/news/blogs-trending-37749007', 'http://www.bbc.com/earth/story/20170619-conservation-success-for-otters-on-the-brink', 'http://www.bbc.com/future/story/20171022-the-hidden-crisis-shaping-life-on-earth', 'http://www.bbc.com/news/blogs-trending-39490637', 'http://www.bbc.com/news/blogs-trending-39142260', 'http://www.bbc.com/news/blogs-trending-36085314', 'http://www.bbc.com/news/blogs-trending-39997949', 'http://www.bbc.com/autos/story/20160907-is-warsaw-the-next-motor-city', 'http://www.bbc.com/earth/story/20160314-filming-with-remotely-operated-cameras', 'http://www.bbc.com/earth/story/20141212-record-year-for-bitterns', 'http://www.bbc.com/future/story/20170822-why-its-not-surprising-that-ship-collisions-still-happen', 'http://www.bbc.com/autos/story/20160211-the-go-kart-for-helicopter-parents', 'http://www.bbc.com/news/blogs-trending-35413576', 'http://www.bbc.com/news/blogs-trending-36133936', 'http://www.bbc.com/autos/story/20160408-nasas-missing-junkyard-rover-goes-to-auction']))
hcl.sort()
HARD_CODED_LINKS = hcl
TOTAL = len(HARD_CODED_LINKS)


@mod_eval_desc.route('/view', methods=["GET", "POST"])
def view_desc():
    return render_template("desc_module/view.html", batch_list=get_all_batch_desc())


@mod_eval_desc.route('/submit', methods=["GET", "POST"])
# @login_required
def submit_desc():
    return render_template(
        "desc_module/submit.html"
    )


@mod_eval_desc.route('/eval')
@login_required
def evaluation_desc():
    eval_list = get_all_desc_eval()
    eval_list.sort()
    return render_template(
        "desc_module/eval.html",
        eval_list=eval_list
    )


def _get_selection_string(selection):
    if selection == 0:
        return 'alinhamento'
    elif selection == 1:
        return 'coref'
    elif selection == 2:
        return 'sinonimos'


@mod_eval_desc.route('/describe_batch', methods=["GET", "POST"])
# @login_required
def describe_batch():
    print([(k,v) for k, v in request.form.items()])
    try:
        links = list(set(request.form["batch_links"].split("\n")))
        links.sort()
        total = len(links)
        batch_name = request.form["batch_name"]
        restriction = request.form["restriction"]
        failed = []
        with open(f'{TMP_DIR}/test_description.csv', 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
            writer.writeheader()

        if request.form["all"] == "1":
            for i, link in enumerate(links):
                desc_batch = create_desc_batch(
                    name=f'{batch_name}_{link}')
                print(f"#####\n\tbegining [{i}/{total}]\n#####")
                link = link.replace('\r', '')
                for selection in [0, 1, 2]:
                    selection_string = _get_selection_string(selection)
                    for method in ['baseline4', 'baseline5']:
                        try:
                            print(f"#####\n\tbegining [{i}/{total} | {method}-{selection_string}]\n#####")
                            response = do_describe(link=link, method=method, select=selection)
                            news_object = response["news"]
                            news_object.fantasy_id = i
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
                            print(f"#####\n\tfinishing [{i+1}/{total} | {method}-{selection_string}]\n#####")
                        except Exception as exc:
                            PrintException()
                            failed.append((link, f'{str(exc)}'))

                print(f"#####\n\tfinishing [{i + 1}/{TOTAL}]\n#####")
                if len(desc_batch.desc_eval_list) != 6:
                    failed.append((link, f'len != 6: {", ".join([de.get_method() for de in desc_batch.desc_eval_list])}'))
        else:
            method = request.form["method"]
            selection = int(request.form["selection"])
            selection_string = _get_selection_string(selection)
            desc_batch = create_desc_batch(
                name=f'{batch_name}_method_{method}_{selection_string}')
            for i, link in enumerate(links):
                try:
                    print(f"#####\n\tbegining [{i}/{total} | {method}-{_get_selection_string(selection)}]\n#####")
                    link = link.replace('\r', '')
                    response = do_describe(link=link, method=method, select=selection)
                    news_object = response["news"]
                    news_object.fantasy_id = i
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
                    print(f"#####\n\tfinishing [{i + 1}/{total} | {method}-{selection_string}]\n#####")
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
@login_required
def eval_desc_batch():
    type_pattern = r"([a-z]*)_"
    radio_pattern = r"^(\w*)(_b)(\d*)(_e)(\d*)"
    print([item for item in request.form.items()])
    batch_id = -1
    de_id = -1
    for tag_id, value in request.form.items():
        str_match = [t(s) for t, s in zip((str,), re.search(type_pattern, tag_id).groups())][0]
        try:
            if str_match == "radio":
                (_, _, batch_id, _, de_id) = [
                    t(s) for t, s in zip((str, str, int, str, int), re.search(radio_pattern, tag_id).groups())
                ]
                de: DescEval = query_by_id(DescEval, de_id)
                de.approve(value=value)
                de.add_self()
            elif str_match == "comment":
                (_, _, batch_id, _, de_id) = [
                    t(s) for t, s in zip((str, str, int, str, int), re.search(radio_pattern, tag_id).groups())
                ]
                de: DescEval = query_by_id(DescEval, de_id)
                de.comments = value
                de.add_self()
            elif str_match == "better":
                (_, _, batch_id, _, de_id) = [
                    t(s) for t, s in zip((str, str, int, str, int), re.search(radio_pattern, tag_id).groups())
                ]
                de: DescEval = query_by_id(DescEval, de_id)
                de.set_compare_baseline(value)
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
            response=json.dumps({"error": str(exc)}),
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
        fields = ['Link', 'Alignment', 'Description', 'AMR', 'Approval', 'Compare', 'Comment']
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()

        eval: DescEval
        for eval in eval_list:
            writer.writerow({
                # 'Title': eval.get_news().get_title(),
                'Link': eval.get_news().get_link(),
                'Alignment': eval.get_desc().get_alignment(),
                'Description': eval.get_desc(),
                'AMR': eval.get_desc().get_amr(),
                # 'Base': eval.get_desc().get_main().get_penman(return_type='str'),
                # 'Others': "\n".join(
                #     [amr.get_penman(return_type='str') for amr in eval.get_desc().get_adjacents()]),
                'Approval': eval.get_approval_string(),
                'Compare': eval.get_compare_baseline(),
                'Comment': eval.get_comment()
            })

    return send_from_directory(BASE_DIR + "/" + STATIC_REL, file_name, as_attachment=True)


def _download_metrics(eval_list):

    def is_valid():
        pass

    file_name = 'metrics_desc.csv'
    with open(file=STATIC_REL + file_name, encoding='utf-8', mode='w+') as metrics_file:
        writer = csv.DictWriter(metrics_file, fieldnames=['Medida', 'Medição', 'Instâncias'])
        writer.writeheader()

        correct = p_correct = incorrect = invalid = 0
        better = equal = worse = 0
        better_v = equal_v = worse_v = 0

        total = len(eval_list)
        e: DescEval
        for e in eval_list:
            if e.compare_baseline == 2:
                better += 1
            elif e.compare_baseline == 1:
                equal += 1
            elif e.compare_baseline == 0:
                worse += 1
            if e.approval == -1:
                invalid +=1
            else:
                if e.approval == 2:
                    correct += 1
                elif e.approval == 1:
                    p_correct += 1
                elif e.approval == 0:
                    incorrect += 1

                if e.compare_baseline == 2:
                    better_v += 1
                elif e.compare_baseline == 1:
                    equal_v += 1
                elif e.compare_baseline == 0:
                    worse_v += 1

        valid = total - invalid

        writer.writerow({'Medida': 'TOTAL DE DESCRIÇÕES', 'Medição': str(total), 'Instâncias': ''})

        writer.writerow({'Medida': 'CORRETAS', 'Medição': f'{str(correct)}', 'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(approval=2)])})
        writer.writerow({'Medida': 'CORRETAS % válidas', 'Medição': f'{str(correct * 100. / valid)}%',
                         'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(approval=2)])})

        writer.writerow({'Medida': 'PARCIALMENTE CORRETAS', 'Medição': f'{str(p_correct)}', 'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(approval=1)])})
        writer.writerow({'Medida': 'PARCIALMENTE CORRETAS % válidas', 'Medição': f'{str(p_correct * 100. / valid)}%',
                         'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(approval=1)])})

        writer.writerow({'Medida': 'INCORRETAS', 'Medição': f'{str(incorrect)}', 'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(approval=0)])})
        writer.writerow({'Medida': 'INCORRETAS % válidas', 'Medição': f'{str(incorrect * 100. / valid)}%',
                         'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(approval=0)])})

        writer.writerow({'Medida': 'INVÁLIDAS', 'Medição': f'{str(invalid)}', 'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(approval=-1)])})

        writer.writerow({'Medida': 'MELHOR QUE O ALINHAMENTO', 'Medição': f'{str(better)}', 'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(compare_baseline=2)])})
        writer.writerow({'Medida': 'IGUAL AO ALINHAMENTO', 'Medição': f'{str(equal)}', 'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(compare_baseline=1)])})
        writer.writerow({'Medida': 'PIOR QUE O ALINHAMENTO', 'Medição': f'{str(worse)}', 'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(compare_baseline=0)])})

        writer.writerow({'Medida': 'MELHOR QUE O ALINHAMENTO VÁLIDO', 'Medição': f'{str(better_v)}',
                         'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(compare_baseline=2) if de.approval > 0])})
        writer.writerow({'Medida': 'IGUAL AO ALINHAMENTO VÁLIDO', 'Medição': f'{str(equal_v)}',
                         'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(compare_baseline=1) if de.approval > 0])})
        writer.writerow({'Medida': 'PIOR QUE O ALINHAMENTO VÁLIDO', 'Medição': f'{str(worse_v)}',
                         'Instâncias': ', '.join([str(de.id) for de in DescEval.query.filter_by(compare_baseline=0) if de.approval > 0])})

        comments = set([de.comments for de in DescEval.query.all()])
        comments.remove('')

        for c in comments:
            instances = [str(de.id) for de in DescEval.query.filter_by(comments=c)]
            writer.writerow({'Medida': c, 'Medição': str(len(instances)), 'Instâncias': ', '.join(instances)})

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
