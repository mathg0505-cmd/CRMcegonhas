from __future__ import annotations

APP_NAME = "CRM Cegonhas"
PAGE_CONFIG = {"page_title": APP_NAME, "layout": "wide"}

COMMISSION_RATE = 0.12

SHEETS_SCHEMA = {
    "frotas": ["frota_id", "frota_nome", "motorista_nome", "ativa"],
    "viagens": [
        "viagem_id",
        "data_carregamento",
        "data_finalizacao",
        "dias_viagem",
        "frota_id",
        "destino",
        "frete_total",
        "status",
        "mes_competencia",
        "valor_adiantamento",
        "data_adiantamento",
        "valor_quitacao",
        "data_prevista_quitacao",
        "data_quitacao",
        "status_pagamento",
    ],
    "despesas": [
        "despesa_id",
        "data",
        "frota_id",
        "viagem_id",
        "categoria",
        "valor",
        "tipo_pagamento",
        "obs",
    ],
    "tarefas": [
        "tarefa_id",
        "titulo",
        "descricao",
        "status",
        "prioridade",
        "data_criacao",
        "data_limite",
        "data_conclusao",
        "frota_id",
        "viagem_id",
        "responsavel",
    ],
}

TRIP_STATUS_OPTIONS = ["aberta", "finalizada"]
PAYMENT_STATUS_OPTIONS = ["pendente", "parcial", "quitado"]
TASK_STATUS_OPTIONS = ["aberta", "em_andamento", "concluida", "cancelada"]
TASK_PRIORITY_OPTIONS = ["baixa", "media", "alta"]
