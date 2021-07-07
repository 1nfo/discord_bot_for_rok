from peewee import ForeignKeyField, CharField

from models import Base
from models.player import Player


class UsedName(Base):
    player = ForeignKeyField(Player, backref='used_names')
    name = CharField()
