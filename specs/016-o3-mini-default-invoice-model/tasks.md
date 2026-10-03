# Tarefas de Implementação - Feature 016: o3-mini como Modelo Padrão

- [ ] T001 [Config] Atualizar `invoice_model: str = "o3-mini"` em `src/contas/config.py` e `.env.example`
- [ ] T002 [UI] Definir `"o3-mini"` como primeira opção do selectbox em `src/contas/ui/app.py`
- [ ] T003 [Tests] Atualizar asserções de modelo default em `tests/unit/test_invoice_parser.py`
- [ ] T004 [Verification] Executar `uv run ruff check` e `uv run pytest tests/unit/test_invoice_parser.py`
