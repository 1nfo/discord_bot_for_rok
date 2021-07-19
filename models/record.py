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
        T4CavDeath = 't4_cav_death'
        T4InfDeath = 't4_inf_death'
        T4ArcDeath = 't4_archer_death'
        T4SiegeDeath = 't4_siege_death'
        T5CavDeath = 't5_cav_death'
        T5InfDeath = 't5_inf_death'
        T5ArcDeath = 't5_archer_death'
        T5SiegeDeath = 't5_siege_death'
        Stage1 = 'stage1'
        Stage2 = 'stage2'
        Stage3 = 'stage3'

    player = ForeignKeyField(Player, index=True, backref='records')
    event = ForeignKeyField(RecordingEvent, backref='records')
    type = CharField(choices=Type.__members__.values())
    value = CharField()
