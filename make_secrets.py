import json
from pathlib import Path

# 1) Nome exato do seu arquivo JSON (que está dentro da pasta do projeto)
JSON_FILE = "aqueous-aileron-488400-q3-6a981ec0b5be.json"

# 2) Nome da sua planilha
SPREADSHEET_NAME = "Cópia de CRM Cegonhas "

# 3) ID da planilha (da URL que você mandou)
SPREADSHEET_ID = "1hiQC6knPad0vQyDk_2LW_z8I2KCk6bc9HMZ8-Tl63yo"

json_path = Path(JSON_FILE)
if not json_path.exists():
    raise FileNotFoundError(
        f"Não achei o arquivo JSON aqui: {json_path.resolve()}\n"
        "Coloque o JSON dentro da pasta do projeto (mesmo nível do app.py)."
    )

# Lê o JSON
data = json.loads(json_path.read_text(encoding="utf-8"))

# IMPORTANTÍSSIMO: TOML não aceita quebras de linha reais dentro de aspas
private_key_escaped = data["private_key"].replace("\n", "\\n")

toml = (
    f'spreadsheet_name = "{SPREADSHEET_NAME}"\n'
    f'spreadsheet_id = "{SPREADSHEET_ID}"\n\n'
    f"[gcp_service_account]\n"
    f'type = "{data["type"]}"\n'
    f'project_id = "{data["project_id"]}"\n'
    f'private_key_id = "{data["private_key_id"]}"\n'
    f'private_key = "{private_key_escaped}"\n'
    f'client_email = "{data["client_email"]}"\n'
    f'client_id = "{data["client_id"]}"\n'
    f'token_uri = "{data["token_uri"]}"\n'
)

out_path = Path(".streamlit") / "secrets.toml"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(toml, encoding="utf-8")

print("OK! secrets.toml gerado em:", out_path.resolve())
print("Usando o JSON:", json_path.name)
print("Service account:", data["client_email"])
print("Planilha ID:", SPREADSHEET_ID)