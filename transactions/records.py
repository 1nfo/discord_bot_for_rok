from models import db, Record, Player, RecordingEvent


@db.atomic()
def create_record(gov_id, record_type, value, event, datetime_created=None):
    player = Player.get(gov_id=gov_id)
    defaults = {
        'value': value,
    }
    if datetime_created:
        defaults['datetime_created'] = datetime_created

    return Record.get_or_create(player=player, event=event, type=record_type, defaults=defaults)


@db.atomic()
def create_records(gov_id, event=None, datetime_created=None, **records):
    player = Player.get(gov_id=gov_id)
    event = event or RecordingEvent.current_event()

    for record_type, value in records.items():
        record = Record.get_or_none(
            player=player,
            event=event,
            type=Record.Type(record_type),
        )

        record.value = value
        if datetime_created:
            record.datetime_created = datetime_created
        record.save()
