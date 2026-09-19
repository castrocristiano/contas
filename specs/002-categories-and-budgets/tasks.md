# Tasks de Implementação: Gestão de Categorias e Orçamentos

**Feature**: `002-categories-and-budgets` | **Branch**: `feature/002-categories-and-budgets`
**Spec**: [spec.md](./spec.md) | **Plano**: [plan.md](./plan.md) | **Modelo de Dados**: [data-model.md](./data-model.md)

---

## Fase 1: Setup & Fundação (Modelo e Banco)

**Propósito**: Modelagem da entidade `Budget`, migração no banco de dados e exportação de tipos.

**⚠️ CRÍTICO**: Nenhuma história de usuário pode ser iniciada até esta fase estar completa.

- [x] T001 Criar modelo `Budget(SQLModel, table=True)` em `src/contas/models/budget.py` com campos `id: uuid.UUID`, `category_id: uuid.UUID` (FK→category, `ondelete="RESTRICT"`), `amount: Decimal` (`NUMERIC(14,2)`, `gt=0`), `month: int` (1..12), `year: int`, `created_at: datetime` (timezone-aware UTC) e `UniqueConstraint("category_id", "month", "year", name="uq_budget_category_period")`
- [x] T002 [P] Atualizar `src/contas/models/__init__.py` exportando `Budget`
- [x] T003 Atualizar `migrations/env.py` garantindo importação de `Budget` e gerar migração: `uv run alembic revision --autogenerate -m "create budget table"`
- [x] T004 Aplicar migração no banco de dados: `uv run alembic upgrade head`

**Checkpoint**: Tabela `budget` criada com constraint única no PostgreSQL.

---

## Fase 2: História de Usuário 1 — Gerenciamento de Categorias (P1) 🎯 MVP

**Meta**: Permitir cadastrar e listar categorias com filtros via tools MCP.

**Teste Independente**: Chamar `create_category` ("Supermercado", `expense`) e `list_categories`, verificando retorno com status ativo e sem duplicidade.

### Schemas & Exceções

- [x] T005 [P] [US1] Criar `src/contas/schemas/category.py`: `CreateCategoryInput(BaseModel)` com `name: str` (1..100) e `category_type: CategoryType`; `CategoryResponse(BaseModel)`; `ListCategoriesInput(BaseModel)` com `category_type: CategoryType | None` e `include_inactive: bool = False`; `ListCategoriesResponse(BaseModel)`
- [x] T006 [P] [US1] Atualizar `src/contas/tools/errors.py`: adicionar `CategoryAlreadyExistsError` e tratamento de erros

### Implementação

- [x] T007 [US1] Criar `src/contas/tools/categories.py`: implementar `create_category(payload: CreateCategoryInput)` e `list_categories(payload: ListCategoriesInput)`
- [x] T008 [US1] Registrar `register_category_tools(mcp)` em `src/contas/server.py`

### Testes

- [x] T009 [P] [US1] Criar testes unitários para schemas de categoria em `tests/unit/test_category_schemas.py`
- [x] T010 [US1] Criar testes de integração para as tools de categoria em `tests/integration/test_category_tools.py`

**Checkpoint**: `create_category` e `list_categories` funcionam e passam nos testes.

---

## Fase 3: História de Usuário 2 — Definição de Orçamentos Mensais (P2)

**Meta**: Permitir estipular limites de gastos para categorias por mês e ano.

**Teste Independente**: Chamar `set_budget` para uma categoria com valor R$ 500,00 para 09/2026 e verificar persistência.

### Schemas

- [x] T011 [P] [US2] Criar `src/contas/schemas/budget.py`: `SetBudgetInput(BaseModel)` com `category_id: UUID`, `amount: str` (positivo com até 2 casas), `month: int` (1..12) e `year: int`; `BudgetResponse(BaseModel)`

### Implementação

- [x] T012 [US2] Criar `src/contas/tools/budgets.py`: implementar tool `set_budget(payload: SetBudgetInput)` com criação ou atualização (*upsert*) do orçamento
- [x] T013 [US2] Registrar `register_budget_tools(mcp)` em `src/contas/server.py`

### Testes

- [x] T014 [P] [US2] Criar testes unitários de schemas de budget em `tests/unit/test_budget_schemas.py`
- [x] T015 [US2] Criar testes de integração para `set_budget` em `tests/integration/test_budget_tools.py`

**Checkpoint**: Orçamentos podem ser criados e atualizados com validações estritas.

---

## Fase 4: História de Usuário 3 — Acompanhamento de Execução Orçamentária (P3)

**Meta**: Fornecer status comparativo entre orçado, gasto realizado, saldo restante e percentual de consumo.

**Teste Independente**: Registrar transações de despesa em uma categoria com orçamento e chamar `get_budget_status`, validando os cálculos exatos.

### Schemas

- [x] T016 [P] [US3] Adicionar schemas em `src/contas/schemas/budget.py`: `GetBudgetStatusInput(BaseModel)` com `month: int | None`, `year: int | None`, `category_id: UUID | None`; `BudgetItemStatus(BaseModel)`, `BudgetSummary(BaseModel)`, `BudgetStatusResponse(BaseModel)`

### Implementação

- [x] T017 [US3] Adicionar tool `get_budget_status(payload: GetBudgetStatusInput)` em `src/contas/tools/budgets.py` agregando despesas da categoria no período e calculando métricas
- [x] T018 [US3] Criar testes de cálculo e execução orçamentária em `tests/integration/test_budget_execution.py`

**Checkpoint**: `get_budget_status` retorna métricas exatas e detecta limites excedidos.

---

## Fase 5: Polish & Finalização

- [x] T019 [P] Atualizar `README.md` com a documentação das novas ferramentas MCP (`create_category`, `list_categories`, `set_budget`, `get_budget_status`)
- [x] T020 Validar cenário completo do [quickstart.md](./quickstart.md)
- [x] T021 Executar `uv run ruff check .` e `uv run ruff format .`
- [x] T022 Executar suíte completa de testes com `uv run pytest -v`
- [ ] T023 Fazer commit e push do branch `feature/002-categories-and-budgets`
