from transactions import events
import settings

from .sheet import upsert_new_sheet


def dump_records_to_sheet(event_name, sheet_id):
    event = events.get_events(event_name)[0]
    df = events.report_event(event)

    data = [
        [f'Collected around: {event.datetime_created.date()}'],
        list(map(str, df.columns))
    ]
    data.extend([list(arr) for arr in df.to_numpy()])

    gid = upsert_new_sheet(sheet_id, event_name, data=data)

    return f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={gid}'
