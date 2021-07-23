import enum

from peewee import ForeignKeyField

from models import Base, EnumField
from models.identity import Identity
from models.player import Player


class IdentityLinkage(Base):
    class Type(enum.IntEnum):
        Main = 1
        Sub = 2

    player = ForeignKeyField(Player, unique=True)
    identity = ForeignKeyField(Identity)
    type = EnumField(enum_type=Type, default=Type.Main)
