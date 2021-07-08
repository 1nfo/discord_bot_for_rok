import enum

from peewee import ForeignKeyField, CharField

from models import Base
from models.player import Player
from models.recording_event import RecordingEvent


class Record(Base):
    @enum.unique
    class Type(str, enum.Enum):
        T4 = 't4'
        T5 = 't5'
        Death = 'death'
        Power = 'power'
        Honor = 'honor'
        Stage1 = 'stage1'
        Stage2 = 'stage2'
        Stage3 = 'stage3'

    player = ForeignKeyField(Player, index=True, backref='records')
    event = ForeignKeyField(RecordingEvent)
    type = CharField(choices=Type.__members__.values())
    value = CharField()
