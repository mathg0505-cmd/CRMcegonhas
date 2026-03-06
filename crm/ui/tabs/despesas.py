from __future__ import annotations

from datetime import date

import streamlit as st

from crm.domain.normalizers import normalize_frotas, normalize_viagens
from crm.infra.sheets import SheetStore


EXPENSE_CATEGORIES = ["Abastecimento", "Manutencao", "Comissao", "Pedagio", "Outros"]
PAYMENT_TYPES = ["a_vista", "a_pagar"]


def render_despesas_tab(store: SheetStore) -> None:
    df_frotas = normalize_frotas(store.read_tab("frotas"))
    df_viagens = normalize_viagens(store.read_tab("viagens"))
    df_despesas_raw = store.read_tab("despesas")

    st.subheader("Despesas cadastradas")
    st.dataframe(df_despesas_raw, use_container_width=True)

    st.divider()
    st.subheader("Lancar despesa")

    frotas_options = [f"{row.frota_id} - {row.frota_nome}" for row in df_frotas.itertuples(index=False)] if not df_frotas.empty else []
    viagens_options = df_viagens["viagem_id"].tolist() if not df_viagens.empty else []

    with st.form("form_despesa", clear_on_submit=True):
        expense_date = st.date_input("Data", value=date.today())

        if frotas_options:
            frota_selected = st.selectbox("Frota", options=frotas_options)
        else:
            st.info("Cadastre uma frota antes de lancar despesas.")
            frota_selected = ""

        trip_id = st.selectbox("Viagem (opcional)", options=[""] + viagens_options)
        category = st.selectbox("Categoria", options=EXPENSE_CATEGORIES)
        amount = st.text_input("Valor (ex.: 1200,00)")
        payment_type = st.selectbox("Tipo de pagamento", options=PAYMENT_TYPES)
        notes = st.text_input("Observacao (opcional)")
        submitted = st.form_submit_button("Salvar despesa")

    if not submitted:
        return

    if not frotas_options:
        st.error("Cadastre ao menos uma frota antes.")
        return

    if not amount.strip():
        st.error("Informe o valor da despesa.")
        return

    next_id = store.next_numeric_id("despesas", "despesa_id")
    frota_id = frota_selected.split("-")[0].strip()

    store.append_dict(
        "despesas",
        {
            "despesa_id": str(next_id),
            "data": str(expense_date),
            "frota_id": frota_id,
            "viagem_id": str(trip_id),
            "categoria": category,
            "valor": amount.strip(),
            "tipo_pagamento": payment_type,
            "obs": notes.strip(),
        },
    )

    st.success("Despesa registrada com sucesso.")
    st.rerun()
