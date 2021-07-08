from discord.utils import cached_property
from peewee import CharField, ForeignKeyField

from models import Base
from models.alliance import Alliance


class Player(Base):
    gov_id = CharField(unique=True, index=True)
    current_name = CharField(unique=True, index=True)
    nick_name = CharField(null=True)
    alliance = ForeignKeyField(Alliance, null=True)

    def get_notes(self, type_name='', limit=20):
        from models.player_note import PlayerNote, NoteType
        note_types = NoteType.startswith(type_name)
        return self.notes.where(PlayerNote.type.in_(note_types)).order_by(PlayerNote.id.desc()).limit(limit)

    @cached_property
    def alliance_name(self):
        return self.alliance.name if self.alliance else None
