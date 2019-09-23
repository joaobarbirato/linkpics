from app import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())


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
        if isinstance(object, list):
            model.extend(object)
        else:
            model.append(object)

    return model


def _add_session(object):
    if object is not None:
        if isinstance(object, list):
            db.session.add_all(object)
        else:
            db.session.add(object)


def add_db_alignments_from_list(list_alignments):
    db.session.add_all(list_alignments)