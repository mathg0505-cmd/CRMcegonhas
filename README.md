# CRM Cegonhas

Aplicacao Streamlit para controle operacional e financeiro de frotas, viagens, despesas e tarefas.

## Arquitetura

- `app.py`: entrypoint e montagem das abas.
- `crm/core`: configuracoes globais, schema, estilos e utilitarios de formatacao.
- `crm/infra`: integracao com Google Sheets e camada `SheetStore`.
- `crm/domain`: normalizacao de dados e metricas de negocio.
- `crm/ui/tabs`: cada aba da interface em modulo separado.

## Beneficios da estrutura

- Evolucao por versao: cada nova feature entra em modulo proprio sem misturar com outras areas.
- Ajuste visual rapido: CSS centralizado em `crm/core/styles.py`.
- Menor risco de quebra: leitura/escrita no Sheets padronizada por schema em `SheetStore`.
- Expansao funcional: nova aba de tarefas pronta para evolucao de backlog e acompanhamento operacional.

## Execucao

```bash
streamlit run app.py
```
