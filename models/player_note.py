from peewee import CharField
from peewee import ForeignKeyField, TextField

from models import Base
from .player import Player


class NoteType(Base):
    name = CharField(unique=True)

    @classmethod
    def startswith(cls, name):
        return NoteType.select().where(NoteType.name.startswith(name.upper()))


class PlayerNote(Base):
    player = ForeignKeyField(Player, backref='notes')
    type = ForeignKeyField(NoteType)
    content = TextField()
