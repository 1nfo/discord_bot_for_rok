import enum

from peewee import CharField, IntegerField

from models import Base


class RecordingEvent(Base):
    @enum.unique
    class Status(enum.IntEnum):
        Pending = 0
        Open = 1
        Closed = 2

    name = CharField(unique=True)
    status = IntegerField(choices=Status.__members__.values(), default=Status.Pending)

    @classmethod
    def current_event(cls):
        return cls.filter(status=cls.Status.Open).order_by(cls.id.desc()).first()
