# Tasks: Refatoração para Clean Architecture (012-clean-architecture-refactoring)

- [x] 1. Spec & Planejamento SDD
  - [x] 1.1 Criar `specs/012-clean-architecture-refactoring/spec.md`
  - [x] 1.2 Criar `specs/012-clean-architecture-refactoring/plan.md`
  - [x] 1.3 Criar `specs/012-clean-architecture-refactoring/tasks.md`

- [x] 2. Camada de Domínio (`src/contas/domain`)
  - [x] 2.1 Criar entidades de domínio puras (`Account`, `Transaction`, `Category`, `Budget`)
  - [x] 2.2 Criar Value Objects, Enums e Exceções de Domínio (`src/contas/domain/errors.py`)
  - [x] 2.3 Adicionar testes unitários para regras das entidades de domínio

- [x] 3. Camada de Aplicação (`src/contas/application`)
  - [x] 3.1 Definir contratos de portas (`ports/repositories.py`)
  - [x] 3.2 Migrar DTOs (Data Transfer Objects) e Schemas de validação
  - [x] 3.3 Implementar Casos de Uso de Contas (`CreateAccount`, `ListAccounts`, `DeleteAccount`, `BulkDeleteAccounts`)
  - [x] 3.4 Implementar Casos de Uso de Transações (`RecordTransaction`, `DeleteTransaction`, `GetStatement`, `GetFinancialSummary`, `GetInstallmentPlan`)
  - [x] 3.5 Implementar Casos de Uso de Categorias e Orçamentos (`CreateCategory`, `ListCategories`, `SetBudget`, `GetBudget`)
  - [x] 3.6 Implementar Casos de Uso de Faturas (`ParseInvoice`, `RefineInvoice`)
  - [x] 3.7 Criar repositórios in-memory para testes unitários dos casos de uso
  - [x] 3.8 Implementar Application Container (`src/contas/application/container.py`)

- [x] 4. Camada de Infraestrutura (`src/contas/infrastructure`)
  - [x] 4.1 Reorganizar modelos SQLAlchemy em `infrastructure/db/models`
  - [x] 4.2 Implementar repositórios SQLAlchemy concretos aderentes às portas (`SQLAlchemyAccountRepository`, `SQLAlchemyCategoryRepository`, `SQLAlchemyTransactionRepository`, `SQLAlchemyBudgetRepository`)

- [x] 5. Camada de Interfaces / Adaptadores de Entrada (`src/contas/tools`, `src/contas/ui`)
  - [x] 5.1 Adaptar ferramentas do MCP Server (`src/contas/tools/*`) para delegar aos casos de uso
  - [x] 5.2 Garantir retrocompatibilidade e aliases para pontos de entrada públicos

- [x] 6. Testes, Qualidade e Validação
  - [x] 6.1 Adicionar testes unitários de casos de uso puros em memória (`tests/unit/test_clean_architecture_use_cases.py`)
  - [x] 6.2 Executar linter e formatador (`uv run ruff check --fix . && uv run ruff format .`)
  - [x] 6.3 Validar 100% de aprovação na suite de testes (`pytest` com 94 testes passando)

