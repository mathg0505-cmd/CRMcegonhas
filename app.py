from __future__ import annotations

from datetime import date, datetime
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="CRM Cegonhas", layout="wide")
COMISSAO_MOTORISTA = 0.12  # 12%

SHEETS_SCHEMA = {
    "frotas": ["frota_id", "frota_nome", "motorista_nome", "ativa"],
    # viagens ganhou colunas para "fechar" e medir duração
    "viagens": [
        "viagem_id",
        "data_carregamento",
        "data_finalizacao",
        "dias_viagem",
        "frota_id",
        "destino",
        "frete_total",
        "status",
    ],
    "despesas": ["despesa_id", "data", "frota_id", "viagem_id", "categoria", "valor", "tipo_pagamento", "obs"],
}

# =========================
# FORMAT / PARSING
# =========================
def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def to_float(x) -> float:
    if x is None:
        return 0.0
    s = str(x).strip()
    if not s:
        return 0.0
    if "," in s:  # BR
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def safe_int(x) -> int:
    try:
        return int(str(x).strip())
    except Exception:
        return 0

def parse_date_any(x) -> date | None:
    """
    Aceita 'YYYY-MM-DD' (que é o que gravamos), ou vazio.
    """
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

# =========================
# GOOGLE AUTH + SHEETS
# =========================
def get_gspread_client() -> gspread.Client:
    if "gcp_service_account" not in st.secrets:
        st.error("Faltam credenciais: configure [gcp_service_account] em .streamlit/secrets.toml")
        st.stop()

    service_account_info = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(creds)

def open_spreadsheet(gc: gspread.Client) -> gspread.Spreadsheet:
    if "spreadsheet_id" in st.secrets and str(st.secrets["spreadsheet_id"]).strip():
        return gc.open_by_key(st.secrets["spreadsheet_id"])
    if "spreadsheet_name" in st.secrets and str(st.secrets["spreadsheet_name"]).strip():
        return gc.open(st.secrets["spreadsheet_name"])
    st.error("Configure no secrets.toml: spreadsheet_id (recomendado) ou spreadsheet_name.")
    st.stop()

def ensure_tabs_exist_and_migrate(sh: gspread.Spreadsheet) -> None:
    """
    Cria abas se não existirem.
    Se existirem, garante que o cabeçalho contenha as colunas esperadas (migração).
    """
    existing = {ws.title for ws in sh.worksheets()}

    for tab_name, headers in SHEETS_SCHEMA.items():
        if tab_name not in existing:
            ws = sh.add_worksheet(title=tab_name, rows=2000, cols=max(10, len(headers)))
            ws.append_row(headers)
            continue

        ws = sh.worksheet(tab_name)
        values = ws.get_all_values()

        if not values:
            ws.append_row(headers)
            continue

        current_header = values[0]

        # Migração: se faltarem colunas novas, adiciona no final
        missing = [h for h in headers if h not in current_header]
        if missing:
            new_header = current_header + missing
            ws.update("1:1", [new_header])  # atualiza a linha 1
            # também precisa garantir que linhas antigas tenham o mesmo número de colunas
            # (gspread/Sheets aceitam linhas mais curtas; aqui não precisa preencher)

def read_tab_as_df(sh: gspread.Spreadsheet, tab_name: str) -> pd.DataFrame:
    try:
        ws = sh.worksheet(tab_name)
    except WorksheetNotFound:
        return pd.DataFrame(columns=SHEETS_SCHEMA.get(tab_name, []))

    values = ws.get_all_values()
    if not values:
        return pd.DataFrame(columns=SHEETS_SCHEMA.get(tab_name, []))

    header = values[0]
    rows = values[1:]
    if not rows:
        return pd.DataFrame(columns=header)

    return pd.DataFrame(rows, columns=header)

def append_row(sh: gspread.Spreadsheet, tab_name: str, row: list) -> None:
    ws = sh.worksheet(tab_name)
    ws.append_row(row, value_input_option="USER_ENTERED")

def update_row_by_key(
    sh: gspread.Spreadsheet,
    tab_name: str,
    key_column: str,
    key_value: str,
    updates: dict,
) -> bool:
    """
    Atualiza uma linha na aba tab_name onde key_column == key_value.
    updates: {col_name: new_value}
    Retorna True se atualizou, False se não encontrou.
    """
    ws = sh.worksheet(tab_name)
    values = ws.get_all_values()
    if not values or len(values) < 2:
        return False

    header = values[0]
    if key_column not in header:
        return False

    key_idx = header.index(key_column)
    # procura linha
    target_row_num = None  # 1-indexed no Sheets
    for i, row in enumerate(values[1:], start=2):
        cell = row[key_idx] if key_idx < len(row) else ""
        if str(cell).strip() == str(key_value).strip():
            target_row_num = i
            break

    if target_row_num is None:
        return False

    # aplica updates célula a célula
    for col_name, new_val in updates.items():
        if col_name not in header:
            continue
        col_idx = header.index(col_name) + 1  # 1-indexed
        ws.update_cell(target_row_num, col_idx, new_val)

    return True

# =========================
# BUSINESS LOGIC
# =========================
def normalize_frotas(df_frotas: pd.DataFrame) -> pd.DataFrame:
    if df_frotas.empty:
        return pd.DataFrame(columns=SHEETS_SCHEMA["frotas"])
    df = df_frotas.copy()
    for c in SHEETS_SCHEMA["frotas"]:
        if c not in df.columns:
            df[c] = ""
    df["frota_id"] = df["frota_id"].astype(str).str.strip()
    df["frota_nome"] = df["frota_nome"].astype(str).str.strip()
    df["motorista_nome"] = df["motorista_nome"].astype(str).str.strip()
    df["ativa"] = df["ativa"].astype(str).str.strip()
    return df[SHEETS_SCHEMA["frotas"]]

def normalize_viagens(df_viagens: pd.DataFrame) -> pd.DataFrame:
    if df_viagens.empty:
        return pd.DataFrame(columns=SHEETS_SCHEMA["viagens"])
    df = df_viagens.copy()
    for c in SHEETS_SCHEMA["viagens"]:
        if c not in df.columns:
            df[c] = ""
    df["frota_id"] = df["frota_id"].astype(str).str.strip()
    df["viagem_id"] = df["viagem_id"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip().str.lower()
    df["frete_total_num"] = df["frete_total"].apply(to_float)

    # datas
    df["data_carregamento_dt"] = df["data_carregamento"].apply(parse_date_any)
    df["data_finalizacao_dt"] = df["data_finalizacao"].apply(parse_date_any)

    # dias_viagem calculado se possível
    def calc_days(row):
        ini = row["data_carregamento_dt"]
        fim = row["data_finalizacao_dt"]
        if ini and fim:
            return (fim - ini).days
        return None

    df["dias_viagem_calc"] = df.apply(calc_days, axis=1)
    return df

def normalize_despesas(df_despesas: pd.DataFrame) -> pd.DataFrame:
    if df_despesas.empty:
        return pd.DataFrame(columns=SHEETS_SCHEMA["despesas"])
    df = df_despesas.copy()
    for c in SHEETS_SCHEMA["despesas"]:
        if c not in df.columns:
            df[c] = ""
    df["frota_id"] = df["frota_id"].astype(str).str.strip()
    df["viagem_id"] = df["viagem_id"].astype(str).str.strip()
    df["categoria"] = df["categoria"].astype(str).str.strip()
    df["valor_num"] = df["valor"].apply(to_float)
    return df

def calc_resumo_global(df_viagens: pd.DataFrame, df_despesas: pd.DataFrame) -> dict:
    receita = float(df_viagens["frete_total_num"].sum()) if not df_viagens.empty else 0.0

    despesas = 0.0
    if not df_despesas.empty:
        dd = df_despesas.copy()
        dd = dd[dd["categoria"].str.lower() != "comissão"]
        despesas = float(dd["valor_num"].sum())

    comissao = receita * COMISSAO_MOTORISTA
    lucro = receita - despesas - comissao
    return {"receita": receita, "despesas": despesas, "comissao": comissao, "lucro": lucro}

def resumo_por_frota(df_frotas: pd.DataFrame, df_viagens: pd.DataFrame, df_despesas: pd.DataFrame) -> pd.DataFrame:
    f = normalize_frotas(df_frotas)

    if df_viagens.empty:
        rec = pd.DataFrame(columns=["frota_id", "receita"])
    else:
        rec = (
            df_viagens.groupby("frota_id", as_index=False)["frete_total_num"]
            .sum()
            .rename(columns={"frete_total_num": "receita"})
        )

    if df_despesas.empty:
        des = pd.DataFrame(columns=["frota_id", "despesas"])
    else:
        dd = df_despesas[df_despesas["categoria"].str.lower() != "comissão"]
        des = (
            dd.groupby("frota_id", as_index=False)["valor_num"]
            .sum()
            .rename(columns={"valor_num": "despesas"})
        )

    out = f.merge(rec, on="frota_id", how="left").merge(des, on="frota_id", how="left")
    out["receita"] = out["receita"].fillna(0.0).astype(float)
    out["despesas"] = out["despesas"].fillna(0.0).astype(float)
    out["comissao"] = out["receita"] * COMISSAO_MOTORISTA
    out["lucro"] = out["receita"] - out["despesas"] - out["comissao"]
    out = out.sort_values(by="lucro", ascending=False).reset_index(drop=True)

    return out[["frota_id", "frota_nome", "motorista_nome", "receita", "despesas", "comissao", "lucro"]]

# =========================
# UI
# =========================
st.title("CRM Cegonhas (MVP)")

gc = get_gspread_client()
sheet = open_spreadsheet(gc)
ensure_tabs_exist_and_migrate(sheet)

tab_dashboard, tab_frotas, tab_viagens, tab_despesas = st.tabs(
    ["📊 Dashboard", "🚚 Frotas", "🧾 Viagens", "💸 Despesas"]
)

# ==========
# DASHBOARD
# ==========
with tab_dashboard:
    df_frotas_raw = read_tab_as_df(sheet, "frotas")
    df_viagens_raw = read_tab_as_df(sheet, "viagens")
    df_despesas_raw = read_tab_as_df(sheet, "despesas")

    df_frotas = normalize_frotas(df_frotas_raw)
    df_viagens = normalize_viagens(df_viagens_raw)
    df_despesas = normalize_despesas(df_despesas_raw)

    st.subheader("Visão geral")
    colf1, colf2, colf3 = st.columns([2, 2, 3])

    with colf1:
        frota_options = ["Todas"] + [f"{r.frota_id} - {r.frota_nome}" for r in df_frotas.itertuples(index=False)]
        frota_sel = st.selectbox("Filtrar por frota", options=frota_options)

    with colf2:
        status_sel = st.selectbox("Status das viagens", ["todas", "aberta", "finalizada"])

    with colf3:
        st.caption("Dica: use Status = 'aberta' para acompanhar só o que está em andamento.")

    dfv = df_viagens.copy()
    dfd = df_despesas.copy()

    if frota_sel != "Todas":
        frota_id_sel = frota_sel.split("-")[0].strip()
        dfv = dfv[dfv["frota_id"] == frota_id_sel]
        dfd = dfd[dfd["frota_id"] == frota_id_sel]

    if status_sel != "todas":
        dfv = dfv[dfv["status"] == status_sel]

    resumo = calc_resumo_global(dfv, dfd)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita (Fretes)", brl(resumo["receita"]))
    c2.metric("Despesas", brl(resumo["despesas"]))
    c3.metric("Comissão (12%)", brl(resumo["comissao"]))
    c4.metric("Lucro", brl(resumo["lucro"]))

    st.divider()
    st.subheader("Resultado por frota")
    df_resumo_frotas = resumo_por_frota(df_frotas, df_viagens, df_despesas)
    st.dataframe(df_resumo_frotas, use_container_width=True)

    if not df_resumo_frotas.empty:
        chart_df = df_resumo_frotas.set_index("frota_id")[["receita", "despesas", "lucro"]]
        st.bar_chart(chart_df)

# ==========
# FROTAS
# ==========
with tab_frotas:
    df_frotas_raw = read_tab_as_df(sheet, "frotas")
    st.subheader("Lista de frotas")
    st.dataframe(df_frotas_raw, use_container_width=True)

    st.divider()
    st.subheader("Adicionar frota")
    with st.form("form_frota", clear_on_submit=True):
        frota_id = st.text_input("Número da frota (ex.: 1831)")
        frota_nome = st.text_input("Nome da frota (ex.: TNorte)")
        motorista_nome = st.text_input("Nome do motorista (ex.: Luciano)")
        ativa = st.checkbox("Ativa", value=True)
        submitted = st.form_submit_button("Salvar")

    if submitted:
        if not frota_id.strip() or not frota_nome.strip():
            st.error("Preencha pelo menos: Número da frota e Nome da frota.")
        else:
            append_row(sheet, "frotas", [frota_id.strip(), frota_nome.strip(), motorista_nome.strip(), str(ativa).upper()])
            st.success("Frota adicionada! Recarregue a página (F5) para ver na lista.")

# ==========
# VIAGENS
# ==========
with tab_viagens:
    df_frotas = normalize_frotas(read_tab_as_df(sheet, "frotas"))
    df_viagens_raw = read_tab_as_df(sheet, "viagens")
    df_viagens = normalize_viagens(df_viagens_raw)

    st.subheader("Viagens")

    colv1, colv2 = st.columns([2, 3])
    with colv1:
        filtro_status = st.selectbox("Mostrar", ["abertas", "finalizadas", "todas"])
    with colv2:
        st.caption("Aqui você consegue fechar viagens e registrar a data de finalização (para medir duração).")

    df_show = df_viagens_raw.copy()
    if not df_viagens.empty and "status" in df_viagens.columns:
        if filtro_status == "abertas":
            df_show = df_viagens_raw[df_viagens["status"] == "aberta"]
        elif filtro_status == "finalizadas":
            df_show = df_viagens_raw[df_viagens["status"] == "finalizada"]

    st.dataframe(df_show, use_container_width=True)

    st.divider()
    st.subheader("Adicionar viagem (a partir da nota)")

    frotas_disp = [f"{r.frota_id} - {r.frota_nome}" for r in df_frotas.itertuples(index=False)] if not df_frotas.empty else []

    with st.form("form_viagem", clear_on_submit=True):
        viagem_id = st.text_input("ID da viagem (ex.: 295701)")
        data_carregamento = st.date_input("Data do carregamento", value=date.today())

        if frotas_disp:
            frota_sel = st.selectbox("Frota", options=frotas_disp)
        else:
            st.info("Cadastre uma frota primeiro na aba 'Frotas'.")
            frota_sel = ""

        destino = st.text_input("Destino (ex.: CABO DE SANTO AGOSTINHO/PE)")
        frete_total = st.text_input("Frete total (ex.: 38416,32 ou 38416.32)")
        submitted = st.form_submit_button("Salvar viagem (aberta)")

    if submitted:
        if not frotas_disp:
            st.error("Cadastre uma frota antes.")
        elif not viagem_id.strip() or not frete_total.strip():
            st.error("Preencha pelo menos: ID da viagem e Frete total.")
        else:
            frota_id = frota_sel.split("-")[0].strip()
            append_row(
                sheet,
                "viagens",
                [
                    viagem_id.strip(),
                    str(data_carregamento),
                    "",      # data_finalizacao
                    "",      # dias_viagem
                    frota_id,
                    destino.strip(),
                    frete_total.strip(),
                    "aberta",
                ],
            )
            st.success("Viagem adicionada como ABERTA! Recarregue a página (F5).")

    st.divider()
    st.subheader("Fechar viagem")

    # lista só viagens abertas
    abertas = []
    if not df_viagens.empty:
        abertas = df_viagens[df_viagens["status"] == "aberta"]["viagem_id"].tolist()

    if not abertas:
        st.info("Não há viagens abertas no momento.")
    else:
        with st.form("form_fechar_viagem"):
            viagem_fechar = st.selectbox("Selecione a viagem aberta", options=abertas)
            data_finalizacao = st.date_input("Data de finalização (entrega)", value=date.today())
            submitted_close = st.form_submit_button("Fechar viagem")

        if submitted_close:
            # calcula dias
            row = df_viagens[df_viagens["viagem_id"] == str(viagem_fechar)].iloc[0]
            ini = row["data_carregamento_dt"]
            fim = data_finalizacao
            dias = ""
            if ini:
                dias = str((fim - ini).days)

            ok = update_row_by_key(
                sheet,
                tab_name="viagens",
                key_column="viagem_id",
                key_value=str(viagem_fechar),
                updates={
                    "status": "finalizada",
                    "data_finalizacao": str(data_finalizacao),
                    "dias_viagem": dias,
                },
            )
            if ok:
                st.success("Viagem fechada! Recarregue a página (F5) para ver atualizado.")
            else:
                st.error("Não consegui encontrar essa viagem para atualizar (confira o ID).")

# ==========
# DESPESAS
# ==========
with tab_despesas:
    df_frotas = normalize_frotas(read_tab_as_df(sheet, "frotas"))
    df_viagens = normalize_viagens(read_tab_as_df(sheet, "viagens"))
    df_despesas_raw = read_tab_as_df(sheet, "despesas")

    st.subheader("Despesas cadastradas")
    st.dataframe(df_despesas_raw, use_container_width=True)

    st.divider()
    st.subheader("Lançar despesa")

    frotas_disp = [f"{r.frota_id} - {r.frota_nome}" for r in df_frotas.itertuples(index=False)] if not df_frotas.empty else []
    viagens_disp = df_viagens["viagem_id"].tolist() if not df_viagens.empty else []

    with st.form("form_despesa", clear_on_submit=True):
        data_despesa = st.date_input("Data", value=date.today())

        if frotas_disp:
            frota_sel = st.selectbox("Frota", options=frotas_disp)
        else:
            st.info("Cadastre uma frota primeiro na aba 'Frotas'.")
            frota_sel = ""

        viagem_id = st.selectbox("Viagem (opcional)", options=[""] + viagens_disp)
        categoria = st.selectbox("Categoria", ["Abastecimento", "Manutenção", "Comissão"])
        valor = st.text_input("Valor (ex.: 1200,00 ou 1200.00)")
        tipo_pagamento = st.selectbox("Tipo de pagamento", ["a_vista", "a_pagar"])
        obs = st.text_input("Observação (opcional)")
        submitted = st.form_submit_button("Salvar despesa")

    if submitted:
        if not frotas_disp:
            st.error("Cadastre uma frota antes.")
        elif not valor.strip():
            st.error("Informe o valor.")
        else:
            next_id = 1
            if not df_despesas_raw.empty and "despesa_id" in df_despesas_raw.columns:
                ids = [safe_int(x) for x in df_despesas_raw["despesa_id"].tolist()]
                next_id = (max(ids) + 1) if ids else 1

            frota_id = frota_sel.split("-")[0].strip() if frota_sel else ""

            append_row(
                sheet,
                "despesas",
                [
                    str(next_id),
                    str(data_despesa),
                    frota_id,
                    str(viagem_id),
                    categoria,
                    valor.strip(),
                    tipo_pagamento,
                    obs.strip(),
                ],
            )
            st.success("Despesa lançada! Recarregue a página (F5) para ver na lista.")