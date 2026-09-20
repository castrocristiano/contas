# Tasks: Interface Web com Streamlit (004-streamlit-frontend)

**Feature**: `004-streamlit-frontend` | **Branch**: `feature/004-streamlit-frontend`
**Spec**: [spec.md](./spec.md) | **Plano**: [plan.md](./plan.md)

---

## Fase 1: Dependências & Estrutura Base

- [x] T001 Adicionar `streamlit>=1.35.0` ao `pyproject.toml` e executar `uv sync`
- [x] T002 Adicionar script de entrada `contas-ui = "contas.ui.app:run_app"` e comando de execução no `README.md`
- [x] T003 Criar estrutura de pacotes `src/contas/ui/__init__.py`

---

## Fase 2: Camada de Serviços da UI

- [x] T004 Criar `src/contas/ui/services.py` com funções para carregar contas, extrato, categorias, orçamentos e registrar transações e metas
- [x] T005 Criar testes unitários para a camada de serviços em `tests/unit/test_ui_services.py`

---

## Fase 3: História de Usuário 1 — Dashboard e Extrato (P1) 🎯 MVP

- [x] T006 Criar componentes visuais e layout em `src/contas/ui/app.py` com cards de patrimônio total e saldos por conta
- [x] T007 Implementar visualização do extrato detalhado com filtros por período e conta na aba principal

---

## Fase 4: História de Usuário 2 — Formulários de Lançamento (P2)

- [x] T008 Implementar formulário de Nova Transação (Receita, Despesa e Transferência) com suporte a compras parceladas
- [x] T009 Implementar formulários modais/seções para cadastro de Nova Conta e Nova Categoria

---

## Fase 5: História de Usuário 3 — Orçamentos e Planos de Parcelamento (P3)

- [x] T010 Implementar seção de Orçamentos com barras de progresso de consumo mensal e alertas de teto excedido
- [x] T011 Implementar visualização de planos de parcelamento ativos com saldo devedor restante

---

## Fase 6: Polish & Finalização

- [x] T012 Atualizar `README.md` documentando como executar o frontend via `uv run streamlit run src/contas/ui/app.py`
- [x] T013 Validar linter e formatação: `uv run ruff check .` e `uv run ruff format .`
- [x] T014 Executar suíte completa de testes: `uv run pytest -v`
- [ ] T015 Fazer commit e push do branch `feature/004-streamlit-frontend`

