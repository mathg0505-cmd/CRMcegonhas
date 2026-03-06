from __future__ import annotations

from datetime import date

import streamlit as st

from crm.domain.normalizers import normalize_frotas, normalize_viagens
from crm.infra.sheets import SheetStore


def render_viagens_tab(store: SheetStore) -> None:
    df_frotas = normalize_frotas(store.read_tab("frotas"))
    df_viagens_raw = store.read_tab("viagens")
    df_viagens = normalize_viagens(df_viagens_raw)

    st.subheader("Viagens")
    col1, col2 = st.columns([2, 3])

    with col1:
        display_filter = st.selectbox("Mostrar", ["abertas", "finalizadas", "todas"])

    with col2:
        st.caption("Cadastre novas viagens e feche viagens abertas sem sair da mesma tela.")

    display_df = df_viagens_raw.copy()
    if not df_viagens.empty:
        if display_filter == "abertas":
            display_df = df_viagens_raw[df_viagens["status"] == "aberta"]
        elif display_filter == "finalizadas":
            display_df = df_viagens_raw[df_viagens["status"] == "finalizada"]

    st.dataframe(display_df, use_container_width=True)

    st.divider()
    st.subheader("Adicionar viagem")

    frotas_options = [f"{row.frota_id} - {row.frota_nome}" for row in df_frotas.itertuples(index=False)] if not df_frotas.empty else []

    with st.form("form_viagem", clear_on_submit=True):
        viagem_id = st.text_input("ID da viagem (ex.: 295701)")
        data_carregamento = st.date_input("Data de carregamento", value=date.today())

        if frotas_options:
            frota_selected = st.selectbox("Frota", options=frotas_options)
        else:
            st.info("Cadastre ao menos uma frota primeiro.")
            frota_selected = ""

        destino = st.text_input("Destino")
        frete_total = st.text_input("Frete total (ex.: 38416,32)")
        submitted_new = st.form_submit_button("Salvar viagem")

    if submitted_new:
        if not frotas_options:
            st.error("Cadastre uma frota antes de registrar viagem.")
        elif not viagem_id.strip() or not frete_total.strip():
            st.error("Preencha pelo menos ID da viagem e Frete total.")
        elif not df_viagens.empty and df_viagens["viagem_id"].eq(viagem_id.strip()).any():
            st.error("Esse ID de viagem ja existe.")
        else:
            frota_id = frota_selected.split("-")[0].strip()
            store.append_dict(
                "viagens",
                {
                    "viagem_id": viagem_id.strip(),
                    "data_carregamento": str(data_carregamento),
                    "data_finalizacao": "",
                    "dias_viagem": "",
                    "frota_id": frota_id,
                    "destino": destino.strip(),
                    "frete_total": frete_total.strip(),
                    "status": "aberta",
                    "mes_competencia": "",
                    "valor_adiantamento": "",
                    "data_adiantamento": "",
                    "valor_quitacao": "",
                    "data_prevista_quitacao": "",
                    "data_quitacao": "",
                    "status_pagamento": "pendente",
                },
            )
            st.success("Viagem adicionada como aberta.")
            st.rerun()

    st.divider()
    st.subheader("Fechar viagem")
    open_trips = df_viagens[df_viagens["status"] == "aberta"]["viagem_id"].tolist() if not df_viagens.empty else []

    if not open_trips:
        st.info("Nao ha viagens abertas no momento.")
        return

    with st.form("form_fechar_viagem"):
        trip_to_close = st.selectbox("Viagem aberta", options=open_trips)
        final_date = st.date_input("Data de finalizacao", value=date.today())
        submitted_close = st.form_submit_button("Fechar viagem")

    if not submitted_close:
        return

    trip_row = df_viagens[df_viagens["viagem_id"] == str(trip_to_close)].iloc[0]
    start_date = trip_row["data_carregamento_dt"]
    trip_days = str((final_date - start_date).days) if start_date else ""

    updated = store.update_by_key(
        tab_name="viagens",
        key_column="viagem_id",
        key_value=str(trip_to_close),
        updates={
            "status": "finalizada",
            "data_finalizacao": str(final_date),
            "dias_viagem": trip_days,
        },
    )

    if updated:
        st.success("Viagem fechada com sucesso.")
        st.rerun()
    else:
        st.error("Nao foi possivel localizar a viagem para atualizacao.")
