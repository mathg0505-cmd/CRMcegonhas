from __future__ import annotations

import streamlit as st

from crm.core.config import APP_NAME, PAGE_CONFIG
from crm.core.styles import apply_base_styles
from crm.infra.sheets import get_sheet_store
from crm.ui.tabs.dashboard import render_dashboard_tab
from crm.ui.tabs.despesas import render_despesas_tab
from crm.ui.tabs.frotas import render_frotas_tab
from crm.ui.tabs.tarefas import render_tarefas_tab
from crm.ui.tabs.viagens import render_viagens_tab


def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    apply_base_styles()

    st.title(APP_NAME)
    st.caption("Arquitetura modular para evoluir visual, regras e novas features com menor risco.")

    store = get_sheet_store()

    tab_dashboard, tab_frotas, tab_viagens, tab_despesas, tab_tarefas = st.tabs(
        ["Dashboard", "Frotas", "Viagens", "Despesas", "Tarefas"]
    )

    with tab_dashboard:
        render_dashboard_tab(store)
    with tab_frotas:
        render_frotas_tab(store)
    with tab_viagens:
        render_viagens_tab(store)
    with tab_despesas:
        render_despesas_tab(store)
    with tab_tarefas:
        render_tarefas_tab(store)


if __name__ == "__main__":
    main()
