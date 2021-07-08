import datetime

from peewee import SqliteDatabase, Model, DateTimeField

import settings

db = SqliteDatabase(settings.get('DB_NAME'))


class Base(Model):
    class Meta:
        database = db

    datetime_created = DateTimeField(default=datetime.datetime.now)


from .alliance import Alliance  # noqa
from .identity import Identity  # noqa
from .identity_linkage import IdentityLinkage  # noqa
from .recording_event import RecordingEvent  # noqa
from .record import Record  # noqa
from .player import Player  # noqa
from .player_note import PlayerNote, NoteType  # noqa
from .used_name import UsedName  # noqa

ALL_MODELS = [m for m in globals().values() if isinstance(m, type) and issubclass(m, Base)]


def init_db():
    with db:
        db.create_tables(ALL_MODELS)
        Alliance.get_or_create(name='LEO!')
        Alliance.get_or_create(name='WLF!')
        Alliance.get_or_create(name='LEM!')
        Alliance.get_or_create(name='WAB!')
        Alliance.get_or_create(name='others')

        NoteType.get_or_create(name='BAN')
        NoteType.get_or_create(name='INFO')
        NoteType.get_or_create(name='VIOLATION')
        NoteType.get_or_create(name='CONTRIBUTION')


init_db()
