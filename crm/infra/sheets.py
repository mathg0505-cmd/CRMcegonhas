from __future__ import annotations

from dataclasses import dataclass

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

from crm.core.config import SHEETS_SCHEMA
from crm.core.formatting import safe_int


def _get_gspread_client() -> gspread.Client:
    if "gcp_service_account" not in st.secrets:
        st.error("Credenciais ausentes: configure [gcp_service_account] em .streamlit/secrets.toml.")
        st.stop()

    service_account_info = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(credentials)


def _open_spreadsheet(client: gspread.Client) -> gspread.Spreadsheet:
    if "spreadsheet_id" in st.secrets and str(st.secrets["spreadsheet_id"]).strip():
        return client.open_by_key(str(st.secrets["spreadsheet_id"]).strip())

    if "spreadsheet_name" in st.secrets and str(st.secrets["spreadsheet_name"]).strip():
        return client.open(str(st.secrets["spreadsheet_name"]).strip())

    st.error("Configure no secrets.toml: spreadsheet_id (recomendado) ou spreadsheet_name.")
    st.stop()


def ensure_tabs_exist_and_migrate(spreadsheet: gspread.Spreadsheet) -> None:
    existing_tabs = {worksheet.title for worksheet in spreadsheet.worksheets()}

    for tab_name, headers in SHEETS_SCHEMA.items():
        if tab_name not in existing_tabs:
            worksheet = spreadsheet.add_worksheet(title=tab_name, rows=2000, cols=max(10, len(headers)))
            worksheet.append_row(headers)
            continue

        worksheet = spreadsheet.worksheet(tab_name)
        values = worksheet.get_all_values()

        if not values:
            worksheet.append_row(headers)
            continue

        current_header = values[0]
        missing_columns = [column for column in headers if column not in current_header]

        if missing_columns:
            worksheet.update("1:1", [current_header + missing_columns])


def read_tab_as_df(spreadsheet: gspread.Spreadsheet, tab_name: str) -> pd.DataFrame:
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except WorksheetNotFound:
        return pd.DataFrame(columns=SHEETS_SCHEMA.get(tab_name, []))

    values = worksheet.get_all_values()
    if not values:
        return pd.DataFrame(columns=SHEETS_SCHEMA.get(tab_name, []))

    header = values[0]
    rows = values[1:]

    if not rows:
        return pd.DataFrame(columns=header)

    return pd.DataFrame(rows, columns=header)


def update_row_by_key(
    spreadsheet: gspread.Spreadsheet,
    tab_name: str,
    key_column: str,
    key_value: str,
    updates: dict,
) -> bool:
    worksheet = spreadsheet.worksheet(tab_name)
    values = worksheet.get_all_values()

    if not values or len(values) < 2:
        return False

    header = values[0]
    if key_column not in header:
        return False

    key_index = header.index(key_column)
    target_row_number = None

    for row_number, row in enumerate(values[1:], start=2):
        cell_value = row[key_index] if key_index < len(row) else ""
        if str(cell_value).strip() == str(key_value).strip():
            target_row_number = row_number
            break

    if target_row_number is None:
        return False

    for column_name, new_value in updates.items():
        if column_name not in header:
            continue
        col_index = header.index(column_name) + 1
        worksheet.update_cell(target_row_number, col_index, new_value)

    return True


@dataclass
class SheetStore:
    spreadsheet: gspread.Spreadsheet

    def read_tab(self, tab_name: str) -> pd.DataFrame:
        return read_tab_as_df(self.spreadsheet, tab_name)

    def append_dict(self, tab_name: str, payload: dict) -> None:
        headers = SHEETS_SCHEMA.get(tab_name, [])
        row = [payload.get(column, "") for column in headers]
        worksheet = self.spreadsheet.worksheet(tab_name)
        worksheet.append_row(row, value_input_option="USER_ENTERED")

    def update_by_key(self, tab_name: str, key_column: str, key_value: str, updates: dict) -> bool:
        return update_row_by_key(
            spreadsheet=self.spreadsheet,
            tab_name=tab_name,
            key_column=key_column,
            key_value=key_value,
            updates=updates,
        )

    def next_numeric_id(self, tab_name: str, id_column: str) -> int:
        dataframe = self.read_tab(tab_name)
        if dataframe.empty or id_column not in dataframe.columns:
            return 1

        ids = [safe_int(value) for value in dataframe[id_column].tolist()]
        return max(ids) + 1 if ids else 1


@st.cache_resource(show_spinner=False)
def get_sheet_store() -> SheetStore:
    client = _get_gspread_client()
    spreadsheet = _open_spreadsheet(client)
    ensure_tabs_exist_and_migrate(spreadsheet)
    return SheetStore(spreadsheet=spreadsheet)
