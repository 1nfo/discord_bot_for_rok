import enum

from peewee import ForeignKeyField, CharField

from models import Base
from models.player import Player
from models.recording_event import RecordingEvent


class Record(Base):
    @enum.unique
    class Type(str, enum.Enum):
        T4 = 'T4'
        T5 = 'T5'
        Death = 'Death'
        Power = 'Power'
        Honor = 'Honor'
        Stage1 = 'Stage1'
        Stage2 = 'Stage2'
        Stage3 = 'Stage3'

    player = ForeignKeyField(Player, index=True, backref='records')
    event = ForeignKeyField(RecordingEvent)
    type = CharField(choices=Type.__members__.values())
    value = CharField()
