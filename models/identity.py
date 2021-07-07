import enum

from peewee import IntegerField, CharField

from models import Base


class Identity(Base):
    @enum.unique
    class Type(enum.IntEnum):
        Discord = 1

    type = IntegerField(choices=Type.__members__.values(), default=Type.Discord)
    name = CharField(null=True)
    external_id = CharField(unique=True)
