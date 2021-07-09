from models import db, NoteType, PlayerNote


@db.atomic()
def create_new_note_type(type_name):
    if not type_name.isalpha():
        raise ValueError('note type must be alphabetic')

    return NoteType.create(name=type_name.upper())


@db.atomic()
def add_player_note(gov_id, type_name, content, datetime_created=None):
    from .players import get_player_by_id
    player = get_player_by_id(gov_id)
    q = NoteType.startswith(type_name)
    c = q.count()
    if c != 1:
        raise ValueError(f'choose note type from {[n.name for n in NoteType.select()]}')

    args = {
        'player': player,
        'type': q.get(),
        'content': content,
    }

    if datetime_created:
        args['datetime_created'] = datetime_created

    return PlayerNote.get_or_create(**args)
