# Plano de Implementação: Compras Parceladas (003-installment-purchases)

**Feature Branch**: `feature/003-installment-purchases` | **Data**: 2026-09-19
**Spec**: [spec.md](./spec.md)

---

## 1. Visão Geral da Arquitetura

A feature estende o modelo `Transaction` para suportar compras parceladas sem introduzir entidades complexas desnecessárias, aplicando o princípio **YAGNI**:
- Campos opcionais adicionados diretamente em `Transaction`:
  - `installment_id: UUID | None` (indexado, para agrupar todas as parcelas da mesma compra)
  - `installment_number: int | None` (1..N)
  - `total_installments: int | None` (N >= 1)
  - `total_amount: Decimal | None` (`NUMERIC(14,2)`)
- Ao chamar `record_transaction` com `total_installments > 1`:
  - Se `installment_number` for omitido ou `1`, o sistema gera um `installment_id = uuid4()`.
  - Calcula a parcela base `floor(total_amount / total_installments)` e adiciona a diferença de centavos na parcela 1.
  - A parcela 1 é gravada como `cleared` (afetando o saldo da conta).
  - As parcelas 2..N são gravadas em batch como `pending` com datas incrementadas mês a mês via função segura de calendário.
- Atualização em `get_statement`: inclusão dos campos de parcelamento em `StatementItem`.
- Nova tool MCP `get_installment_plan`: consulta agregada das parcelas de uma compra pelo `installment_id`.

---

## 2. Fases de Implementação

### Fase 1: Setup & Migração do Banco
1. Alterar `src/contas/models/transaction.py`: adicionar `installment_id`, `installment_number`, `total_installments`, `total_amount`.
2. Gerar migração Alembic: `uv run alembic revision --autogenerate -m "add installment fields to transaction"`.
3. Aplicar migração: `uv run alembic upgrade head`.

### Fase 2: Utilitário de Cálculo de Parcelas
1. Criar helper `src/contas/utils/installments.py`:
   - Cálculo exato de parcelas `Decimal` com compensação de centavos na parcela 1.
   - Cálculo de próxima data mensal com tratamento para finais de mês (ex: 31 jan -> 28 fev).

### Fase 3: Schemas e Tool `record_transaction` (US1)
1. Atualizar `src/contas/schemas/transaction.py`:
   - Campos opcionais em `RecordTransactionInput`: `total_installments`, `installment_number`, `total_amount`.
   - Validações: `total_installments >= 1`, `installment_number >= 1`, coerência entre `amount`, `total_amount` e `total_installments`.
   - Campos no `RecordTransactionResponse`.
2. Atualizar `src/contas/tools/transactions.py`:
   - Gerar parcelas futuras automáticas com `status=pending` e `installment_id`.

### Fase 4: Atualização de Extrato e Tool `get_installment_plan` (US2 & US3)
1. Atualizar `StatementItem` em `src/contas/schemas/transaction.py`.
2. Adicionar schemas `GetInstallmentPlanInput`, `InstallmentPlanResponse`.
3. Implementar tool `get_installment_plan` em `src/contas/tools/transactions.py`.

### Fase 5: Testes e Polish
1. Testes unitários de validação e cálculo em `tests/unit/test_installments.py`.
2. Testes de integração em `tests/integration/test_installment_transactions.py`.
3. Atualizar `README.md` e validar com `ruff` e `pytest`.

