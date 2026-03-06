from __future__ import annotations

import pandas as pd

from crm.core.config import COMMISSION_RATE
from crm.domain.normalizers import normalize_frotas


def calc_global_summary(df_viagens: pd.DataFrame, df_despesas: pd.DataFrame) -> dict:
    receita = float(df_viagens["frete_total_num"].sum()) if not df_viagens.empty else 0.0

    despesas = 0.0
    if not df_despesas.empty:
        no_commission = df_despesas[df_despesas["categoria_key"] != "comissao"]
        despesas = float(no_commission["valor_num"].sum())

    comissao = receita * COMMISSION_RATE
    lucro = receita - despesas - comissao

    return {
        "receita": receita,
        "despesas": despesas,
        "comissao": comissao,
        "lucro": lucro,
    }


def summary_by_frota(
    df_frotas: pd.DataFrame,
    df_viagens: pd.DataFrame,
    df_despesas: pd.DataFrame,
) -> pd.DataFrame:
    frotas = normalize_frotas(df_frotas)

    if df_viagens.empty:
        receita = pd.DataFrame(columns=["frota_id", "receita"])
    else:
        receita = (
            df_viagens.groupby("frota_id", as_index=False)["frete_total_num"]
            .sum()
            .rename(columns={"frete_total_num": "receita"})
        )

    if df_despesas.empty:
        despesas = pd.DataFrame(columns=["frota_id", "despesas"])
    else:
        no_commission = df_despesas[df_despesas["categoria_key"] != "comissao"]
        despesas = (
            no_commission.groupby("frota_id", as_index=False)["valor_num"]
            .sum()
            .rename(columns={"valor_num": "despesas"})
        )

    summary = frotas.merge(receita, on="frota_id", how="left").merge(despesas, on="frota_id", how="left")
    summary["receita"] = summary["receita"].fillna(0.0).astype(float)
    summary["despesas"] = summary["despesas"].fillna(0.0).astype(float)
    summary["comissao"] = summary["receita"] * COMMISSION_RATE
    summary["lucro"] = summary["receita"] - summary["despesas"] - summary["comissao"]

    summary = summary.sort_values(by="lucro", ascending=False).reset_index(drop=True)
    return summary[["frota_id", "frota_nome", "motorista_nome", "receita", "despesas", "comissao", "lucro"]]


def tasks_summary(df_tarefas: pd.DataFrame) -> dict:
    if df_tarefas.empty:
        return {"abertas": 0, "em_andamento": 0, "concluidas": 0, "canceladas": 0}

    status = df_tarefas["status"].astype(str).str.lower()
    return {
        "abertas": int((status == "aberta").sum()),
        "em_andamento": int((status == "em_andamento").sum()),
        "concluidas": int((status == "concluida").sum()),
        "canceladas": int((status == "cancelada").sum()),
    }
