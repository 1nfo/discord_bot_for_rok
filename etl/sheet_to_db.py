import datetime

import settings
from etl import etl_job
from models import Player, Record, RecordingEvent
from settings.constants import Sheet
from transactions.notes import add_player_note
from transactions.players import upsert_player
from transactions.records import create_record
from .sheet import get_sheet_data

KVK3_BACK_FILL_EVENT_NAME = "kvk 3 back fill"
KVK3_BACK_FILL_DATE = datetime.datetime(2021, 5, 12)


def pull_930x_kvk3_member_sheet():
    sheet = Sheet(
        id='1sYXnaOVIeD1tmittd_zuVSZlJATlgpgtjInAYlMCqng',
        name='members',
        start_range='A3',
        end_range='H900',
        col_id='Governor ID',
        col_name='Governor Name',
        col_rank='Rank',
    )
    data = get_sheet_data(sheet)

    for i in data.index:
        player = upsert_player(data[sheet.col_id][i], data[sheet.col_name][i])
        add_player_note(player.gov_id, 'INFO', 'Was in KvK3', KVK3_BACK_FILL_DATE)


def pull_930x_kvk3_kill_sheet():
    sheet = settings.get('KILL_SHEET')
    data = get_sheet_data(sheet)

    event, _ = RecordingEvent.get_or_create(
        name=KVK3_BACK_FILL_EVENT_NAME,
        defaults={
            'status': RecordingEvent.Status.Closed,
            'datetime_created': KVK3_BACK_FILL_DATE,
        }
    )

    def _create_record(player_, record_type, value):
        if value:
            return create_record(player_.gov_id, record_type, value, event, KVK3_BACK_FILL_DATE)

    for i in data.index:
        player = Player.get(data[sheet.col_id][i])
        _create_record(player, Record.Type.T4, data[sheet.col_t4][i])
        _create_record(player, Record.Type.T5, data[sheet.col_t5][i])
        _create_record(player, Record.Type.Death, data[sheet.col_death][i])
        _create_record(player, Record.Type.Power, data[sheet.col_power][i])
