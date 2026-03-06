from __future__ import annotations

import streamlit as st

from crm.core.formatting import brl
from crm.domain.metrics import calc_global_summary, summary_by_frota, tasks_summary
from crm.domain.normalizers import (
    normalize_despesas,
    normalize_frotas,
    normalize_tarefas,
    normalize_viagens,
)
from crm.infra.sheets import SheetStore


def render_dashboard_tab(store: SheetStore) -> None:
    df_frotas = normalize_frotas(store.read_tab("frotas"))
    df_viagens = normalize_viagens(store.read_tab("viagens"))
    df_despesas = normalize_despesas(store.read_tab("despesas"))
    df_tarefas = normalize_tarefas(store.read_tab("tarefas"))

    st.subheader("Visao geral")
    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        frota_options = ["Todas"] + [f"{row.frota_id} - {row.frota_nome}" for row in df_frotas.itertuples(index=False)]
        frota_selected = st.selectbox("Filtrar por frota", options=frota_options)

    with col2:
        status_selected = st.selectbox("Status das viagens", options=["todas", "aberta", "finalizada"])

    with col3:
        st.caption("Use os filtros para comparar resultado por frota e viagens em andamento.")

    viagens_filtered = df_viagens.copy()
    despesas_filtered = df_despesas.copy()

    if frota_selected != "Todas":
        frota_id = frota_selected.split("-")[0].strip()
        viagens_filtered = viagens_filtered[viagens_filtered["frota_id"] == frota_id]
        despesas_filtered = despesas_filtered[despesas_filtered["frota_id"] == frota_id]

    if status_selected != "todas":
        viagens_filtered = viagens_filtered[viagens_filtered["status"] == status_selected]

    financial_summary = calc_global_summary(viagens_filtered, despesas_filtered)
    tasks_kpis = tasks_summary(df_tarefas)

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Receita", brl(financial_summary["receita"]))
    kpi2.metric("Despesas", brl(financial_summary["despesas"]))
    kpi3.metric("Comissao (12%)", brl(financial_summary["comissao"]))
    kpi4.metric("Lucro", brl(financial_summary["lucro"]))
    kpi5.metric("Tarefas abertas", tasks_kpis["abertas"] + tasks_kpis["em_andamento"])

    st.divider()
    st.subheader("Resultado por frota")
    summary_frotas = summary_by_frota(df_frotas, df_viagens, df_despesas)
    st.dataframe(summary_frotas, use_container_width=True)

    if not summary_frotas.empty:
        chart_data = summary_frotas.set_index("frota_id")[["receita", "despesas", "lucro"]]
        st.bar_chart(chart_data)
