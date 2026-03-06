from __future__ import annotations

from datetime import date

import streamlit as st

from crm.core.config import TASK_PRIORITY_OPTIONS, TASK_STATUS_OPTIONS
from crm.domain.normalizers import normalize_frotas, normalize_tarefas, normalize_viagens
from crm.infra.sheets import SheetStore


def _task_option_label(task_row) -> str:
    return f"{task_row.tarefa_id} - {task_row.titulo} ({task_row.status})"


def render_tarefas_tab(store: SheetStore) -> None:
    df_tarefas_raw = store.read_tab("tarefas")
    df_tarefas = normalize_tarefas(df_tarefas_raw)
    df_frotas = normalize_frotas(store.read_tab("frotas"))
    df_viagens = normalize_viagens(store.read_tab("viagens"))

    st.subheader("Backlog de tarefas")
    st.dataframe(df_tarefas_raw, use_container_width=True)

    st.divider()
    st.subheader("Nova tarefa")

    frotas_options = [f"{row.frota_id} - {row.frota_nome}" for row in df_frotas.itertuples(index=False)] if not df_frotas.empty else []
    viagens_options = df_viagens["viagem_id"].tolist() if not df_viagens.empty else []

    with st.form("form_tarefa", clear_on_submit=True):
        title = st.text_input("Titulo")
        description = st.text_area("Descricao", height=80)
        priority = st.selectbox("Prioridade", options=TASK_PRIORITY_OPTIONS, index=1)
        owner = st.text_input("Responsavel")
        due_enabled = st.checkbox("Definir data limite", value=False)
        due_date = st.date_input("Data limite", value=date.today(), disabled=not due_enabled)

        frota_selected = st.selectbox("Frota relacionada (opcional)", options=[""] + frotas_options)
        trip_selected = st.selectbox("Viagem relacionada (opcional)", options=[""] + viagens_options)
        submitted_new = st.form_submit_button("Criar tarefa")

    if submitted_new:
        if not title.strip():
            st.error("Informe um titulo para a tarefa.")
        else:
            next_id = store.next_numeric_id("tarefas", "tarefa_id")
            frota_id = frota_selected.split("-")[0].strip() if frota_selected else ""
            data_limite = str(due_date) if due_enabled else ""

            store.append_dict(
                "tarefas",
                {
                    "tarefa_id": str(next_id),
                    "titulo": title.strip(),
                    "descricao": description.strip(),
                    "status": "aberta",
                    "prioridade": priority,
                    "data_criacao": str(date.today()),
                    "data_limite": data_limite,
                    "data_conclusao": "",
                    "frota_id": frota_id,
                    "viagem_id": str(trip_selected),
                    "responsavel": owner.strip(),
                },
            )
            st.success("Tarefa criada com sucesso.")
            st.rerun()

    st.divider()
    st.subheader("Atualizar status")

    if df_tarefas.empty:
        st.info("Nenhuma tarefa cadastrada.")
        return

    option_map = {_task_option_label(row): row.tarefa_id for row in df_tarefas.itertuples(index=False)}

    with st.form("form_tarefa_status"):
        task_selected = st.selectbox("Tarefa", options=list(option_map.keys()))
        new_status = st.selectbox("Novo status", options=TASK_STATUS_OPTIONS)
        submitted_status = st.form_submit_button("Atualizar")

    if not submitted_status:
        return

    tarefa_id = str(option_map[task_selected])
    concluida_em = str(date.today()) if new_status == "concluida" else ""
    updated = store.update_by_key(
        tab_name="tarefas",
        key_column="tarefa_id",
        key_value=tarefa_id,
        updates={"status": new_status, "data_conclusao": concluida_em},
    )

    if updated:
        st.success("Status da tarefa atualizado.")
        st.rerun()
    else:
        st.error("Nao foi possivel atualizar a tarefa selecionada.")
