from peewee import ForeignKeyField

from models import Base
from models.identity import Identity
from models.player import Player


class IdentityLinkage(Base):
    player = ForeignKeyField(Player)
    identity = ForeignKeyField(Identity)
