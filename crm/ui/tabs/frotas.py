from __future__ import annotations

import streamlit as st

from crm.domain.normalizers import normalize_frotas
from crm.infra.sheets import SheetStore


def render_frotas_tab(store: SheetStore) -> None:
    raw = store.read_tab("frotas")
    normalized = normalize_frotas(raw)

    st.subheader("Lista de frotas")
    st.dataframe(raw, use_container_width=True)

    st.divider()
    st.subheader("Adicionar frota")
    with st.form("form_frota", clear_on_submit=True):
        frota_id = st.text_input("Numero da frota (ex.: 1831)")
        frota_nome = st.text_input("Nome da frota (ex.: TNorte)")
        motorista_nome = st.text_input("Motorista (ex.: Luciano)")
        ativa = st.checkbox("Ativa", value=True)
        submitted = st.form_submit_button("Salvar")

    if not submitted:
        return

    if not frota_id.strip() or not frota_nome.strip():
        st.error("Preencha pelo menos Numero da frota e Nome da frota.")
        return

    already_exists = False
    if not normalized.empty:
        already_exists = normalized["frota_id"].eq(frota_id.strip()).any()

    if already_exists:
        st.error("Essa frota ja existe. Use outro identificador.")
        return

    store.append_dict(
        "frotas",
        {
            "frota_id": frota_id.strip(),
            "frota_nome": frota_nome.strip(),
            "motorista_nome": motorista_nome.strip(),
            "ativa": "TRUE" if ativa else "FALSE",
        },
    )
    st.success("Frota adicionada com sucesso.")
    st.rerun()
