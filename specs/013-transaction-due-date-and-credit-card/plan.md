# Plano de Implementação - Feature 013: Data de Vencimento e Tipo de Conta Cartão de Crédito

## 1. Domain & Enums
- Adicionar `CREDIT_CARD = "credit_card"` em `AccountType` (`src/contas/domain/enums.py` e `src/contas/models/account.py`).
- Adicionar `due_date: datetime | None = None` na entidade `Transaction` (`src/contas/domain/entities.py`).
- Adicionar campo `due_date: datetime | None = Field(default=None, nullable=True, index=True)` no modelo ORM `Transaction` (`src/contas/models/transaction.py`).

## 2. Migração do Banco de Dados
- Criar nova migração Alembic para:
  - Adicionar valor `credit_card` e `CREDIT_CARD` ao tipo `account_type_enum`.
  - Adicionar coluna `due_date` na tabela `transaction` com índice.
  - Atualizar registros existentes: `UPDATE transaction SET due_date = transaction_date WHERE due_date IS NULL`.

## 3. Schemas (Pydantic)
- `src/contas/schemas/transaction.py`:
  - `RecordTransactionInput`: adicionar `due_date: str | None = None`.
  - `RecordTransactionResponse`: adicionar `due_date: datetime | None = None`.
  - `GetStatementInput`: adicionar `date_type: str = "transaction_date"` com validação em `("transaction_date", "due_date")`.
  - `StatementPeriod`: adicionar `date_type: str = "transaction_date"`.
  - `StatementItem`: adicionar `due_date: datetime | None = None`.

## 4. Repositório e Casos de Uso
- `src/contas/application/ports/repositories.py`:
  - Atualizar assinatura de `list_by_account` com `date_type: str = "transaction_date"`.
- `src/contas/infrastructure/repositories/transaction.py`:
  - Mapear `due_date` em `_to_domain` e `_to_orm`.
  - Implementar filtragem por `due_date` quando `date_type == "due_date"`.
- `src/contas/application/use_cases/transactions.py`:
  - Em `RecordTransactionUseCase`: calcular `parsed_due_date = datetime.fromisoformat(payload.due_date) if payload.due_date else parsed_date`.
  - Para parcelamentos: calcular `inst_due_date = add_months(parsed_due_date, idx - 1)`.
  - Em `GetStatementUseCase`: passar `date_type=payload.date_type` para `list_by_account` e preencher `due_date` no `StatementItem`.

## 5. UI (Streamlit)
- `src/contas/ui/app.py`:
  - Exibir tipo "Cartão de Crédito" (`credit_card`) no formulário de criação de conta.
  - No extrato: incluir seletor de "Filtrar por" (Data de Lançamento / Data de Vencimento).
  - Na tabela do extrato: exibir colunas "Data" e "Vencimento".
  - Em "Novo Lançamento": incluir campo "Data de Vencimento".

## 6. Chat Financeiro (OpenAI Function Calling)
- `src/contas/services/financial_chat.py`:
  - Tool `create_account`: enum inclui `"credit_card"`.
  - Tool `record_transaction`: aceita `due_date`.
  - Tool `get_statement`: aceita `date_type`.
  - `_execute_read_tool`: repassa `date_type` para `UIService.get_statement`.
  - `UIService.get_statement`: aceita e repassa `date_type`.
  - `SYSTEM_PROMPT`: orientações para pesquisas por vencimento e contas de cartão de crédito.

## 7. Testes
- Testes unitários para schemas (`test_schemas.py`).
- Testes unitários para use cases (`test_clean_architecture_use_cases.py`).
- Testes unitários para chat (`test_financial_chat.py`).
- Testes de integração com banco de dados.
