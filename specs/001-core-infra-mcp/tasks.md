# Tarefas de Implementação: Infraestrutura Base e Servidor MCP de Finanças

**Feature**: `001-core-infra-mcp` | **Branch**: `001-core-infra-mcp`
**Spec**: [spec.md](./spec.md) | **Plano**: [plan.md](./plan.md) | **Modelo de Dados**: [data-model.md](./data-model.md)

---

## Fase 1: Setup — Infraestrutura de Projeto

**Propósito**: Estrutura de diretórios, arquivos de configuração e orquestração de containers.

- [x] T001 Criar estrutura de diretórios `src/contas/db/`, `src/contas/models/`, `src/contas/schemas/`, `src/contas/tools/` e `tests/unit/`, `tests/integration/`
- [x] T002 Criar `podman-compose.yml` com serviço `db` (postgres:16-alpine), volume nomeado `postgres_data`, healthcheck `pg_isready`, rede `contas_network` e `depends_on: condition: service_healthy` — ver [research/infrastructure.md](./research/infrastructure.md)
- [x] T003 [P] Criar `.env.example` com as variáveis `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL` (formato `postgresql+psycopg://...`) e `OPENAI_API_KEY`
- [x] T004 [P] Criar `Dockerfile` para o serviço `mcp-server` baseado em `python:3.12-slim` com instalação via `uv`
- [x] T005 Inicializar Alembic com template assíncrono: `uv run alembic init -t async migrations`
- [x] T006 Adicionar dependência `pydantic-settings>=2.0` ao `pyproject.toml` via `uv add pydantic-settings`

**Checkpoint**: `podman-compose up -d` sobe o PostgreSQL em estado `healthy`. Estrutura de diretórios criada.

---

## Fase 2: Fundação — Configuração, Engine e Modelos de Domínio

**Propósito**: Infraestrutura de banco e modelos que bloqueiam todas as histórias de usuário.

> **⚠️ CRÍTICO**: Nenhuma história de usuário pode ser iniciada até esta fase estar completa.

- [x] T007 Criar `src/contas/config.py` com `Settings(BaseSettings)`: campos `database_url: str`, `openai_api_key: str = ""`, `debug: bool = False`; leitura automática de `.env`
- [x] T008 Criar `src/contas/db/engine.py`: `create_async_engine` com `postgresql+psycopg://`, `pool_pre_ping=True`, `pool_size=10`, `expire_on_commit=False` no `async_sessionmaker` — ver [research/database.md](./research/database.md)
- [x] T009 Criar `src/contas/db/session.py`: `get_session()` como `@asynccontextmanager` com `commit()` automático e `rollback()` em exceção
- [x] T010 [P] Criar `src/contas/models/account.py`: modelo `Account(SQLModel, table=True)` com campos `id: uuid.UUID`, `name: str` (max_length=100), `account_type: AccountType` (Enum nativo `account_type_enum`), `balance: Decimal` (`NUMERIC(14,2)`), `currency: str` (max_length=3, default="BRL"), `is_active: bool` (default=True), `created_at: datetime` (timezone-aware) — ver [data-model.md](./data-model.md)
- [x] T011 [P] Criar `src/contas/models/category.py`: modelo `Category(SQLModel, table=True)` com campos `id: uuid.UUID`, `name: str` (unique, max_length=100), `category_type: CategoryType` (Enum nativo `category_type_enum`), `is_active: bool` (default=True) — ver [data-model.md](./data-model.md)
- [x] T012 Criar `src/contas/models/transaction.py`: modelo `Transaction(SQLModel, table=True)` com campos `id: uuid.UUID`, `amount: Decimal` (`NUMERIC(14,2)`, gt=0), `transaction_type: TransactionType`, `status: TransactionStatus` (default=cleared), `transaction_date: datetime`, `description: str` (max_length=255), `source_account_id: uuid.UUID` (FK→account, `ondelete="RESTRICT"`), `destination_account_id: uuid.UUID | None` (FK→account, `ondelete="RESTRICT"`), `category_id: uuid.UUID | None` (FK→category, `ondelete="RESTRICT"`), `created_at: datetime`; relacionamentos `source_account`, `destination_account` com `foreign_keys` desambiguados e `passive_deletes=True` — ver [data-model.md](./data-model.md)
- [x] T013 Criar `src/contas/models/__init__.py` exportando `Account`, `Category`, `Transaction`, `AccountType`, `CategoryType`, `TransactionType`, `TransactionStatus`
- [x] T014 Configurar `migrations/env.py`: importar todos os modelos (`Account`, `Category`, `Transaction`), definir `target_metadata = SQLModel.metadata`, ler `DATABASE_URL` de variável de ambiente, habilitar `compare_type=True` e `compare_server_default=True` no `context.configure()` — ver [research/database.md](./research/database.md)
- [x] T015 Gerar e aplicar primeira migração: `uv run alembic revision --autogenerate -m "create initial schema"` seguido de `uv run alembic upgrade head`
- [x] T016 Criar `src/contas/__main__.py` com `from contas.server import main; main()` para suporte a `uv run python -m contas`

**Checkpoint**: `uv run alembic upgrade head` sem erros. Tabelas `account`, `category`, `transaction` criadas no PostgreSQL com tipos enum nativos.

---

## Fase 3: História de Usuário 1 — Registro de Transação Financeira (P1) 🎯 MVP

**Meta**: Permitir criar conta e registrar despesas/receitas via tools MCP com persistência e atualização de saldo.

**Teste Independente**: Chamar `create_account` + `record_transaction` (despesa de R$ 35,50 em conta com R$ 100,00) e verificar que `source_account.new_balance == "64.50"`.

### Schemas (Pydantic I/O — separados dos modelos SQLModel)

- [x] T017 [P] [US1] Criar `src/contas/schemas/account.py`: `CreateAccountInput(BaseModel)` com `ConfigDict(extra="forbid", str_strip_whitespace=True)`, campos `name: str` (min_length=1, max_length=100, description obrigatória), `account_type: AccountType`, `initial_balance: str` (default="0.00", description), `currency: str` (default="BRL", pattern `^[A-Z]{3}$`); `AccountResponse(BaseModel)` com os campos de saída — ver [contracts/mcp-tools.md](./contracts/mcp-tools.md)
- [x] T018 [P] [US1] Criar `src/contas/schemas/transaction.py`: `RecordTransactionInput(BaseModel)` com `ConfigDict(extra="forbid")`, campos `amount: str` (description, pattern `^[0-9]+(\.[0-9]{1,2})?$`), `transaction_type: TransactionType`, `source_account_id: str` (UUID), `destination_account_id: str | None` (default=None), `category_id: str | None` (default=None), `description: str` (max_length=255, default=""), `transaction_date: str | None` (ISO 8601, default=None), `status: TransactionStatus` (default=cleared); `model_validator` garantindo `destination_account_id` obrigatório quando `transaction_type == "transfer"` e diferente de `source_account_id` — ver [contracts/mcp-tools.md](./contracts/mcp-tools.md)

### Implementação

- [x] T019 [US1] Criar `src/contas/tools/accounts.py`: função `register_account_tools(mcp: MCPServer)` com tool `create_account(payload: CreateAccountInput)` que persiste `Account` via `get_session()`, converte `initial_balance` de `str` para `Decimal`, retorna `AccountResponse` serializado — ver [research/mcp-sdk.md](./research/mcp-sdk.md)
- [x] T020 [US1] Criar `src/contas/tools/transactions.py`: função `register_transaction_tools(mcp: MCPServer)` com tool `record_transaction(payload: RecordTransactionInput)` que: (1) valida existência e atividade de `source_account` (e `destination_account` se transfer), (2) converte `amount` para `Decimal`, (3) inicia transação de banco, (4) atualiza `balance` da conta de origem (débito para expense/transfer), credita conta de destino se transfer, (5) persiste `Transaction`, (6) retorna resposta com `new_balance` — operação ACID atômica (RF-004)
- [x] T021 [US1] Criar `src/contas/server.py`: instanciar `MCPServer("contas-server")`, chamar `register_account_tools(mcp)`, `register_transaction_tools(mcp)`, função `main()` com `mcp.run()`; logging configurado para `stderr`
- [x] T022 [US1] Criar `src/contas/tools/health.py`: tool `health_check()` sem parâmetros que tenta query simples no banco (`SELECT 1`) via `get_session()`, retorna `{"status": "healthy"|"unhealthy", "database": "connected"|"disconnected", ...}` — ver [contracts/mcp-tools.md](./contracts/mcp-tools.md)
- [x] T023 [US1] Registrar `health_check` no `server.py` via `register_health_tools(mcp)`

### Testes

- [x] T024 [P] [US1] Criar `tests/unit/test_schemas.py`: testes de validação Pydantic — `RecordTransactionInput` rejeita `amount="0.00"`, rejeita `amount="-10"`, rejeita transfer sem `destination_account_id`, rejeita transfer com `source == destination`; `CreateAccountInput` rejeita `name=""`, rejeita `currency="br"`
- [x] T025 [US1] Criar `tests/unit/test_models.py`: testes de enums — `AccountType("checking")` válido, `AccountType("invalid")` lança `ValueError`; `TransactionType` e `TransactionStatus` idem

**Checkpoint**: `uv run pytest -v` passa. `uv run mcp dev src/contas/server.py` abre MCP Inspector. `create_account` + `record_transaction` funcionam. Saldo atualizado corretamente.

---

## Fase 4: História de Usuário 2 — Consulta de Saldos e Extrato (P2)

**Meta**: Permitir listar contas com saldos e consultar extrato de período com resumo financeiro.

**Teste Independente**: Após registrar transações, chamar `get_statement` com período do mês corrente e verificar retorno com transações ordenadas cronologicamente e `summary` correto.

### Schemas

- [x] T026 [P] [US2] Adicionar a `src/contas/schemas/account.py`: `ListAccountsInput(BaseModel)` com `include_inactive: bool = False`; `ListAccountsResponse` com `accounts: list[AccountSummary]`, `total_balance: str`, `currency: str`, `count: int`
- [x] T027 [P] [US2] Adicionar a `src/contas/schemas/transaction.py`: `GetStatementInput(BaseModel)` com `account_id: str`, `start_date: str`, `end_date: str`, `include_pending: bool = False`, `limit: int` (default=50, ge=1, le=500); `model_validator` garantindo `start_date <= end_date`; `GetFinancialSummaryInput(BaseModel)` com `reference_date: str | None = None`

### Implementação

- [x] T028 [US2] Adicionar tool `list_accounts(payload: ListAccountsInput)` em `src/contas/tools/accounts.py`: query `SELECT * FROM account WHERE is_active=True` (ou incluindo inativos), calcula `total_balance` somando via `Decimal`, retorna `ListAccountsResponse`
- [x] T029 [US2] Adicionar tool `get_statement(payload: GetStatementInput)` em `src/contas/tools/transactions.py`: valida existência da conta, converte `start_date`/`end_date` para `datetime` com timezone, query `Transaction` filtrada por `source_account_id`, período e (opcionalmente) status, ordenada por `transaction_date ASC`, aplica `limit`, calcula `summary` (total_income, total_expense, net) via `Decimal`, retorna resposta — ver [contracts/mcp-tools.md](./contracts/mcp-tools.md)
- [x] T030 [US2] Adicionar tool `get_financial_summary(payload: GetFinancialSummaryInput)` em `src/contas/tools/transactions.py`: lista todas contas ativas com saldos, calcula `total_assets` via `Decimal`, retorna resposta consolidada

**Checkpoint**: `list_accounts` retorna contas com `total_balance` correto. `get_statement` retorna extrato ordenado com `summary` preciso. `get_financial_summary` consolida patrimônio total.

---

## Fase 5: História de Usuário 3 — Validação Estrita e Proteção contra Dados Inválidos (P3)

**Meta**: Garantir que todos os erros de entrada retornem códigos estruturados sem alterar o banco.

**Teste Independente**: Submeter lançamentos inválidos (valor zero, conta inexistente, transfer sem destino) e verificar resposta com código de erro estruturado e banco inalterado.

### Implementação

- [ ] T031 [US3] Criar `src/contas/tools/errors.py`: exceções customizadas `ValidationError`, `AccountNotFoundError`, `CategoryNotFoundError`, `TransferSameAccountError`, `DatabaseError` com código (`error_code`) e mensagem estruturada — ver contratos de erro em [contracts/mcp-tools.md](./contracts/mcp-tools.md)
- [ ] T032 [US3] Adicionar tratamento de erros em `src/contas/tools/accounts.py` e `src/contas/tools/transactions.py`: capturar `AccountNotFoundError` (conta inexistente ou inativa), `TransferSameAccountError`, erros de FK do PostgreSQL (`IntegrityError`), erros de conexão; retornar estrutura `{"error": {"code": "...", "message": "...", "details": {...}}}` — ver [contracts/mcp-tools.md](./contracts/mcp-tools.md)
- [ ] T033 [US3] Adicionar `model_validator` em `RecordTransactionInput` em `src/contas/schemas/transaction.py`: validar que `amount` é convertível para `Decimal` e `> 0`, rejeitar formatos inválidos como `"abc"`, `"1.555"` (mais de 2 casas decimais), `"0.00"`, `"-5.00"`

### Testes

- [ ] T034 [P] [US3] Criar `tests/integration/test_tools.py`: testes de integração com banco real (SQLite in-memory ou PostgreSQL de teste) — `record_transaction` com `amount="0.00"` retorna erro `VALIDATION_ERROR`; `record_transaction` com `source_account_id` inexistente retorna `ACCOUNT_NOT_FOUND`; transfer com `source == destination` retorna `TRANSFER_SAME_ACCOUNT`; banco permanece inalterado após qualquer erro

**Checkpoint**: Todos os cenários P3 da spec rejeitados com erros estruturados. `uv run pytest -v` 100% verde.

---

## Fase Final: Polish e Concerns Transversais

- [ ] T035 [P] Atualizar `README.md`: adicionar seção "Como executar" com `podman-compose up -d`, `uv run alembic upgrade head`, `uv run mcp dev src/contas/server.py`; seção "Ferramentas MCP disponíveis" com link para [contracts/mcp-tools.md](./specs/001-core-infra-mcp/contracts/mcp-tools.md)
- [ ] T036 [P] Atualizar `.gitignore`: adicionar `postgres_data/`, `.env`, `migrations/versions/*.py` não — manter migrações versionadas
- [ ] T037 Executar validação completa do [quickstart.md](./quickstart.md): cenários P1, P2, P3 e `health_check`
- [ ] T038 Executar `uv run ruff check .` e `uv run ruff format .` — corrigir todos os avisos
- [ ] T039 Fazer commit final com mensagem `feat(001): implementar infraestrutura base e servidor MCP de financas`

---

## Dependências e Ordem de Execução

### Dependências entre Fases

- **Fase 1 (Setup)**: Sem dependências — iniciar imediatamente
- **Fase 2 (Fundação)**: Depende da Fase 1 — **bloqueia todas as histórias**
- **Fase 3 (US1)**: Depende da Fase 2 — pode iniciar em paralelo com Fase 4 e 5 após Fundação
- **Fase 4 (US2)**: Depende da Fase 2 e de `list_accounts`/`record_transaction` da Fase 3
- **Fase 5 (US3)**: Depende da Fase 3 (reusa tools já implementadas)
- **Fase Final**: Depende de todas as histórias completas

### Dependências Internas (Fase 2)

```
T007 (config.py) → T008 (engine.py) → T009 (session.py)
T010 (Account) ┐
T011 (Category) ┤ → T012 (Transaction) → T013 (__init__.py) → T014 (env.py) → T015 (migration)
```

### Dependências Internas (Fase 3 — US1)

```
T017 (schemas/account) ┐
T018 (schemas/transaction) ┘ → T019 (tools/accounts) ┐
                                T020 (tools/transactions) ┤ → T021 (server.py)
                                T022 (tools/health) ────────┘
T024 [P] (test_schemas) → pode rodar após T017/T018
T025 (test_models) → pode rodar após T013
```

---

## Oportunidades de Paralelismo

```bash
# Fase 1 — paralelizável:
T002 (podman-compose.yml) || T003 (.env.example) || T004 (Dockerfile)

# Fase 2 — paralelizável após T007-T009:
T010 (Account) || T011 (Category)  # depois: T012 (Transaction)

# Fase 3 — paralelizável:
T017 (schemas/account) || T018 (schemas/transaction)
T019 (tools/accounts) || T020 (tools/transactions) || T022 (tools/health)
T024 (test_schemas) || T025 (test_models)

# Fase 4 — paralelizável:
T026 (ListAccountsInput) || T027 (GetStatementInput)
```

---

## Estratégia de Implementação

### MVP (apenas US1 — Fase 1 + 2 + 3)

1. Completar Fase 1: Setup
2. Completar Fase 2: Fundação (**crítico — bloqueia tudo**)
3. Completar Fase 3: US1 (create_account + record_transaction)
4. **Parar e validar**: `uv run pytest -v` + MCP Inspector manualmente
5. Commit e push do MVP funcional

### Entrega Incremental

1. Setup + Fundação → banco funcional ✅
2. US1 → MVP com registro de transações ✅
3. US2 → Consultas e extrato ✅
4. US3 → Validação estrita e erros estruturados ✅
5. Polish → Documentação e limpeza ✅

---

## Notas

- `[P]` = tarefas em arquivos diferentes, sem dependências entre si — podem executar em paralelo
- `[USn]` = rastreabilidade da tarefa para a história de usuário correspondente
- Valores monetários: sempre `Decimal` no Python, `NUMERIC(14,2)` no banco, `str` no JSON — nunca `float`
- Logging: exclusivamente para `stderr` no servidor MCP (não contaminar `stdout` com JSON-RPC)
- Soft delete: usar `is_active=False` em `Account` e `Category` — nunca `DELETE` em registros com transações

