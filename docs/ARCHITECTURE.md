# Arquitetura e Evolucao

## Objetivo

Manter o CRM facil de evoluir por versao, com baixo risco de quebrar funcionalidades existentes.

## Camadas

- `crm/core`
  - Configuracoes globais (`config.py`)
  - Estilo visual central (`styles.py`)
  - Conversoes e parsing (`formatting.py`)
- `crm/infra`
  - Integracao com Google Sheets (`sheets.py`)
  - Migracao de schema de abas/colunas
- `crm/domain`
  - Normalizacao dos dados (`normalizers.py`)
  - Calculos de negocio e indicadores (`metrics.py`)
- `crm/ui/tabs`
  - Cada tela em arquivo separado, sem acesso direto a detalhes de gspread

## Regras para evoluir sem quebrar

1. Sempre adicionar novas colunas em `SHEETS_SCHEMA` (`crm/core/config.py`).
2. Sempre atualizar o normalizador correspondente em `crm/domain/normalizers.py`.
3. Evitar chamadas diretas de gspread nas abas; usar `SheetStore`.
4. Preferir `append_dict` ao inves de montar listas manuais de colunas.
5. Colocar novas regras de calculo em `crm/domain`, nunca dentro da UI.
6. Alteracoes visuais devem ir para `crm/core/styles.py`.

## Como adicionar uma nova aba

1. Criar `crm/ui/tabs/nova_aba.py` com funcao `render_nova_aba_tab(store)`.
2. Importar no `app.py`.
3. Adicionar na lista de `st.tabs` e chamar o `render`.
4. Se precisar persistir dados, criar/atualizar schema no `config.py`.
5. Rodar validacao sintatica:

```bash
python -m compileall app.py crm
```

## Evolucao recomendada por versoes

- `v1.x`: consolidar CRUD basico e filtros
- `v2.x`: padronizar testes unitarios para `domain`
- `v3.x`: separar repositorios por entidade (frotas/viagens/despesas/tarefas)
- `v4.x`: dashboards com historico mensal e indicadores de performance
