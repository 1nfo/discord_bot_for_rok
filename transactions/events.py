from collections import defaultdict

from pandas import DataFrame
import numpy as np

from models import RecordingEvent as Event
from transactions import players


def list_all_events():
    return Event.select().order_by(Event.datetime_created.desc())


def add_new_event(name):
    return Event.create(name=name)


def rename(event_id, name):
    return Event.update(name=name).where(Event.id == int(event_id)).execute()


def open_event(event_id):
    assert not Event.filter(status=Event.Status.Open).exists(), 'There is an event open, close it first.'
    return Event.update(status=Event.Status.Open).where(Event.id == event_id).execute()


def close_event():
    assert Event.filter(status=Event.Status.Open).exists(), 'There is no event open.'
    return Event.update(status=Event.Status.Closed).where(Event.status == Event.Status.Open).execute()


def get_events(*event_names):
    if not event_names:
        return Event.select()
    events = []
    for event_name in event_names:
        event = Event.get_or_none(name=event_name)
        if event is None:
            raise ValueError(f'{event_name} is not valid.')
        events.append(event)
    return events


def report_event(event):
    report_data = defaultdict(dict)

    for record in event.records:
        report_data[record.player].update({
            'last_update': f'{record.datetime_created.date()}',
            record.type: record.value,
        })
    return DataFrame([
        dict(
            gov_id=player.gov_id,
            name=player.current_name,
            main_account=players.get_main_account(player.gov_id).current_name,
            alliance=player.alliance_name,
            **records
        )
        for player, records in report_data.items()
    ]).replace(np.nan, '', regex=True)
