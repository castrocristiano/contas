# Tasks: Compras Parceladas (003-installment-purchases)

**Feature**: `003-installment-purchases` | **Branch**: `feature/003-installment-purchases`
**Spec**: [spec.md](./spec.md) | **Plano**: [plan.md](./plan.md)

---

## Fase 1: Setup & Migração do Banco

- [x] T001 Adicionar colunas `installment_id: UUID | None`, `installment_number: int | None`, `total_installments: int | None`, `total_amount: Decimal | None` ao modelo `Transaction` em `src/contas/models/transaction.py`
- [x] T002 Gerar migração Alembic: `uv run alembic revision --autogenerate -m "add installment fields to transaction"`
- [x] T003 Aplicar migração no banco de dados: `uv run alembic upgrade head`

---

## Fase 2: Utilitário de Parcelamento

- [x] T004 Criar utilitário `src/contas/utils/installments.py` com `calculate_installments(total_amount, total_installments)` e `add_months(source_date, months)` com ajuste para último dia do mês
- [x] T005 Criar testes unitários para o utilitário em `tests/unit/test_installments.py`

---

## Fase 3: História de Usuário 1 — Registro de Despesa Parcelada (P1) 🎯 MVP

- [x] T006 Atualizar `src/contas/schemas/transaction.py`: adicionar campos de parcelamento em `RecordTransactionInput` e `RecordTransactionResponse`
- [x] T007 Atualizar `src/contas/tools/transactions.py`: na tool `record_transaction`, se `total_installments > 1`, gerar as parcelas subsequentes com `status=pending` e mesmo `installment_id`
- [x] T008 Criar testes de integração para registro de compras parceladas em `tests/integration/test_installment_transactions.py`

---

## Fase 4: Histórias de Usuário 2 e 3 — Extratos e Consulta de Parcelamento (P2/P3)

- [x] T009 Atualizar `StatementItem` em `src/contas/schemas/transaction.py` e mapeamento em `get_statement`
- [x] T010 Adicionar schemas `GetInstallmentPlanInput` e `InstallmentPlanResponse` em `src/contas/schemas/transaction.py`
- [x] T011 Implementar tool `get_installment_plan` em `src/contas/tools/transactions.py`
- [x] T012 Criar testes para `get_installment_plan` e visualização de parcelas em `tests/integration/test_installment_plan.py`

---

## Fase 5: Polish & Finalização

- [x] T013 Atualizar `README.md` com a nova funcionalidade e ferramenta `get_installment_plan`
- [x] T014 Executar linter e formatação: `uv run ruff check .` e `uv run ruff format .`
- [x] T015 Executar suíte completa de testes: `uv run pytest -v`
- [ ] T016 Fazer commit e push do branch `feature/003-installment-purchases`

