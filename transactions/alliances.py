from models import db, Alliance


@db.atomic()
def create_new_alliance(name):
    return Alliance.create(name)
