from peewee import CharField

from models import Base


class Alliance(Base):
    name = CharField(unique=True)

    def __str__(self):
        return self.name
