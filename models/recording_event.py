import datetime
import enum

from peewee import CharField

from models import Base, EnumField


class RecordingEvent(Base):
    @enum.unique
    class Status(enum.IntEnum):
        Pending = 0
        Open = 1
        Closed = 2

    name = CharField(unique=True)
    status = EnumField(enum_type=Status, default=Status.Pending)

    @classmethod
    def current_event(cls):
        e = cls.filter(status=cls.Status.Open).order_by(cls.datetime_created.desc()).first()
        if e:
            return e
        else:
            return cls.create(status=cls.Status.Open, name=f'auto-event {datetime.datetime.now()}')

    def to_text(self):
        return f'name:{self.name}, status: {self.status.name}, datetime_created: {self.datetime_created}'
