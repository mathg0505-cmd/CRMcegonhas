from __future__ import annotations

import pandas as pd

from crm.core.config import SHEETS_SCHEMA
from crm.core.formatting import normalize_token, parse_date_any, to_float


def _ensure_columns(dataframe: pd.DataFrame, schema_name: str) -> pd.DataFrame:
    expected_columns = SHEETS_SCHEMA[schema_name]

    if dataframe.empty:
        return pd.DataFrame(columns=expected_columns)

    normalized = dataframe.copy()
    for column in expected_columns:
        if column not in normalized.columns:
            normalized[column] = ""

    return normalized


def normalize_frotas(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_columns(dataframe, "frotas")
    df["frota_id"] = df["frota_id"].astype(str).str.strip()
    df["frota_nome"] = df["frota_nome"].astype(str).str.strip()
    df["motorista_nome"] = df["motorista_nome"].astype(str).str.strip()
    df["ativa"] = df["ativa"].astype(str).str.strip()
    return df[SHEETS_SCHEMA["frotas"]]


def normalize_viagens(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_columns(dataframe, "viagens")
    df["viagem_id"] = df["viagem_id"].astype(str).str.strip()
    df["frota_id"] = df["frota_id"].astype(str).str.strip()
    df["status"] = df["status"].apply(normalize_token)
    df["frete_total_num"] = df["frete_total"].apply(to_float)
    df["data_carregamento_dt"] = df["data_carregamento"].apply(parse_date_any)
    df["data_finalizacao_dt"] = df["data_finalizacao"].apply(parse_date_any)
    df["valor_adiantamento_num"] = df["valor_adiantamento"].apply(to_float)
    df["valor_quitacao_num"] = df["valor_quitacao"].apply(to_float)

    def _calc_trip_days(row) -> int | None:
        start = row["data_carregamento_dt"]
        end = row["data_finalizacao_dt"]
        if start and end:
            return (end - start).days
        return None

    df["dias_viagem_calc"] = df.apply(_calc_trip_days, axis=1)
    return df


def normalize_despesas(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_columns(dataframe, "despesas")
    df["despesa_id"] = df["despesa_id"].astype(str).str.strip()
    df["frota_id"] = df["frota_id"].astype(str).str.strip()
    df["viagem_id"] = df["viagem_id"].astype(str).str.strip()
    df["categoria"] = df["categoria"].astype(str).str.strip()
    df["categoria_key"] = df["categoria"].apply(normalize_token)
    df["valor_num"] = df["valor"].apply(to_float)
    return df


def normalize_tarefas(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_columns(dataframe, "tarefas")
    df["tarefa_id"] = df["tarefa_id"].astype(str).str.strip()
    df["titulo"] = df["titulo"].astype(str).str.strip()
    df["status"] = df["status"].apply(normalize_token)
    df["prioridade"] = df["prioridade"].apply(normalize_token)
    df["data_criacao_dt"] = df["data_criacao"].apply(parse_date_any)
    df["data_limite_dt"] = df["data_limite"].apply(parse_date_any)
    df["data_conclusao_dt"] = df["data_conclusao"].apply(parse_date_any)
    return df
