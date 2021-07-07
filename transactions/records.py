from models import Record, db


@db.atomic()
def create_record(player, record_type, value, event, datetime_created=None):
    defaults = {
        'value': value,
    }
    if datetime_created:
        defaults['datetime_created'] = datetime_created

    return Record.get_or_create(player=player, event=event, type=record_type, defaults=defaults)
