import logging
import re

import numpy as np
import pandas as pd
from google.oauth2 import service_account
from googleapiclient import discovery

import settings

logger = logging.getLogger(__name__)

credentials = service_account.Credentials.from_service_account_info(
    settings.get('GOOGLE_SERVICE_ACCOUNT_INFO'),
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = discovery.build('sheets', 'v4', credentials=credentials)


def get_sheet_data(sheet):
    request = service.spreadsheets().values().get(
        spreadsheetId=sheet.id,
        range=sheet.range,
    )

    response = request.execute()

    data = response.get("values")
    columns = data[0]
    df = pd.DataFrame(data, columns=columns).drop(0)

    return df


def upsert_sheet_data(sheet, id, row, data=None, return_message=False):
    if data is None:
        data = get_sheet_data(sheet)
    exists = data[(data[sheet.col_id] == str(id))]
    if exists.empty:
        max_index = 0 if data.index.max() is np.nan else data.index.max()
        data = data.append(pd.Series(row, name=max_index + 1)).fillna('')
        body = {
            'range': sheet.range,
            'majorDimension': 'ROWS',
            'values': [list(data.iloc[-1])]
        }
        request = service.spreadsheets().values().append(
            spreadsheetId=sheet.id,
            range=sheet.range,
            valueInputOption='USER_ENTERED',
            insertDataOption='OVERWRITE',
            body=body,
        )
    else:
        ncol, nrow = re.sub(r'(\w+)(\d+)', r'\1 \2', sheet.start_range).split(' ')
        for k, v in row.items():
            exists.iloc[0][k] = v
        body = {
            'range': f"{sheet.name}!{ncol}{int(nrow) + exists.iloc[0].name}",
            'majorDimension': 'ROWS',
            'values': [list(exists.iloc[0])]
        }
        request = service.spreadsheets().values().update(
            spreadsheetId=sheet.id,
            range=body['range'],
            valueInputOption='USER_ENTERED',
            body=body,
        )

    try:
        request.execute()
    except Exception as e:
        logger.exception(f"{e}")
        if return_message:
            return "There is a problem when updating the data."
        else:
            return False
    else:
        if return_message:
            return f"Data updated."
        else:
            return True
