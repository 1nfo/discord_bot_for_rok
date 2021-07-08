import logging as _logging

from settings import get as _get

LOG_LEVEL = _logging.INFO

DISCORD_TOKEN = _get('DISCORD_TOKEN')
COMMAND_PREFIX = '!'
LISTENING_CHANNELS = ["ask-bot", 'bottest']

APPROVAL_EMOJI = '👍'
DECLINED_EMOJI = '👎'
SUCCEED_EMOJI = '✅'
FAILURE_EMOJI = '❌'

DM_COMMAND_MY_KILL_ENABLED = True
DM_COMMAND_MY_SCORE_ENABLED = True
DM_COMMAND_MY_HONOR_ENABLED = True

GOOGLE_SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "goldbot-309200",
    "private_key_id": _get('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID'),
    "private_key": eval(_get('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY')).encode(),
    "client_email": "sheetdata@goldbot-309200.iam.gserviceaccount.com",
    "client_id": "114813656156467293992",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sheetdata%40goldbot-309200.iam.gserviceaccount.com"
}

IN_GAME_ID_COLUMN_NAME = 'id'


class Sheet:
    def __init__(self, id, name, start_range, end_range, **kwargs):
        self.id = id
        self.name = name
        self.start_range = start_range
        self.end_range = end_range
        self._data = kwargs

    @property
    def range(self):
        return f'{self.name}!{self.start_range}:{self.end_range}'

    def __getattr__(self, item):
        return self._data.get(item)



KILL_SHEET = Sheet(
    id='1sYXnaOVIeD1tmittd_zuVSZlJATlgpgtjInAYlMCqng',
    name='kvk3 - kill and death',
    start_range='A1',
    end_range='H900',
    col_name='name',
    col_id=IN_GAME_ID_COLUMN_NAME,
    col_power='power',
    col_t4='t4',
    col_t5='t5',
    col_death='death',
)

PREKVK_SHEET = Sheet(
    id='1sYXnaOVIeD1tmittd_zuVSZlJATlgpgtjInAYlMCqng',
    name='kvk3 - prev-kek',
    start_range='A1',
    end_range='H900',
    col_name='name',
    col_id=IN_GAME_ID_COLUMN_NAME,
    stage_value='score',
    col_stage1=f'score1',
    col_stage2=f'score2',
    col_stage3=f'score3',
)
