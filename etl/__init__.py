JOBS = {}


def etl_job(f):
    if f.__name__ in JOBS:
        raise KeyError(f'Job {f.__name__} already exists.')

    JOBS[f.__name__] = f
    return f


from .sheet_to_db import *
from .discord_to_db import *
