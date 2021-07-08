from models import db, Alliance


@db.atomic()
def create_new_alliance(name):
    return Alliance.create(name)


@db.atomic()
def list_all_alliance_names():
    return [a.name for a in Alliance.select()]


def get_alliance(name):
    return Alliance.get_or_none(name=name)
