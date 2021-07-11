import enum

from peewee import ForeignKeyField, IntegerField

from models import Base
from models.identity import Identity
from models.player import Player


class IdentityLinkage(Base):
    class Type(enum.IntEnum):
        Main = 1
        Sub = 2

    player = ForeignKeyField(Player, unique=True)
    identity = ForeignKeyField(Identity)
    type = IntegerField(default=Type.Main)
