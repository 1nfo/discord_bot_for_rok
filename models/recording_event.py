import datetime
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
        e = cls.filter(status=cls.Status.Open).order_by(cls.datetime_created.desc()).first()
        if e:
            return e
        else:
            return cls.create(status=cls.Status.Open, name=f'auto-event {datetime.datetime.now()}')

    def to_text(self):
        return f'name:{self.name}, status: {self.Status(self.status).name}, datetime_created: {self.datetime_created}'
