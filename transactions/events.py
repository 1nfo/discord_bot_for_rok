from models import RecordingEvent as Event


def list_all_events():
    return Event.select().tuples()


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
