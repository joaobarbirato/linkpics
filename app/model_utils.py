import linecache
import sys

from app import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

    def save(self):
        _add_session(self)
        _commit_session()


def _add(list_object, element):
    if list_object is None:
        list_object = [element]
    elif isinstance(list_object, list):
        list_object.append(element)
    else:
        list_object = [list_object, element]
    return list_object


def _add_relation(model, object):
    if object is not None:
        if isinstance(object, list) and all(item not in model for item in object):
            model.extend(object)
        else:
            model.append(object)

        # tp = type(model)
        # model = tp(set(model))

    return model


def _add_session(obj):
    if obj is not None:
        if isinstance(obj, list):
            db.session.add_all(obj)
        else:
            db.session.add(obj)


def _commit_session():
    db.session.commit()


def add_db_alignments_from_list(list_alignments):
    db.session.add_all(list_alignments)


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f'EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}')