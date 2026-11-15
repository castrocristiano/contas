# Tasks: Filtros de Quitação e Saldo Projetado no Dashboard e Extratos (023-settlement-filters)

**Input**: Design documents from `/specs/023-settlement-filters/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/statement_and_dashboard_contracts.md](contracts/statement_and_dashboard_contracts.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Tarefa paralelizada (arquivos distintos, sem dependência bloqueante)
- **[Story]**: Mapeamento para as User Stories do [spec.md](spec.md) (`[US1]`, `[US2]`, `[US3]`)
- Arquivos com caminhos exatos

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estrutura base de schemas e configurações compartilhadas

- [x] T001 Verificar ambiente Python/uv e dependências de teste em `pyproject.toml`
- [x] T002 [P] Adicionar `StatementStatusFilter` e evoluir `GetStatementInput` em `src/contas/schemas/transaction.py`
- [x] T003 [P] Criar schemas `AccountBalanceProjection` e `DashboardProjectionsResponse` em `src/contas/schemas/account.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura de acesso a dados que bloqueia as user stories

**⚠️ CRITICAL**: Nenhuma User Story pode ser iniciada antes da conclusão desta fase

- [x] T004 Atualizar a interface `ITransactionRepository` em `src/contas/application/ports/repositories.py` adicionando parâmetro `status_filter: str | None = None` ao método `list_by_account`
- [x] T005 Atualizar a implementação `SQLAlchemyTransactionRepository` em `src/contas/infrastructure/repositories/transaction.py` para aplicar a filtragem SQL por status (`ORMTransaction.status == status_filter`)
- [x] T006 [P] Adicionar método auxiliar no repositório de transações em `src/contas/infrastructure/repositories/transaction.py` para listar transações pendentes de um usuário em determinado período de corte

**Checkpoint**: Camada de persistência pronta para atender o Extrato e o Dashboard

---

## Phase 3: User Story 1 - Filtragem por Status de Quitação no Extrato de Movimentações (Priority: P1) 🎯 MVP

**Goal**: Permitir filtrar o extrato por "Todas as Movimentações", "Apenas Pendentes (ocultar quitadas)" e "Apenas Quitadas", recalculando os resumos financeiros.

**Independent Test**: Executar teste unitário com transações pendentes e quitadas; verificar que ao selecionar `status_filter="pending"`, apenas pendências são retornadas e o resumo financeiro soma estritamente esses lançamentos.

### Tests for User Story 1
- [x] T007 [P] [US1] Criar testes unitários para filtragem do extrato por status em `tests/unit/use_cases/test_get_statement_status_filter.py`

### Implementation for User Story 1
- [x] T008 [US1] Atualizar `GetStatementUseCase` em `src/contas/application/use_cases/transactions.py` para processar `status_filter` e calcular `StatementSummary` sobre as transações filtradas
- [x] T009 [P] [US1] Atualizar a tool MCP `get_statement` em `src/contas/server.py` com o parâmetro `status_filter`
- [x] T010 [US1] Atualizar `UIService.get_statement` em `src/contas/ui/services.py` para propagar o parâmetro `status_filter`
- [x] T011 [US1] Adicionar `st.selectbox` de status de quitação e integrar com a tabela do extrato em `src/contas/ui/app.py`

**Checkpoint**: MVP concluído! Extrato pode ser testado e utilizado independentemente.

---

## Phase 4: User Story 2 - Visão Comparativa de Saldo Atual vs. Saldo Projetado no Dashboard (Priority: P2)

**Goal**: Calcular no Dashboard a projeção de saldo abatendo despesas pendentes e somando receitas pendentes do mês corrente por conta e no patrimônio total.

**Independent Test**: Criar uma conta com R$ 1.000,00 e uma despesa pendente de R$ 250,00; verificar se o saldo projetado exibe exatamente R$ 750,00 e o saldo atual se mantém em R$ 1.000,00.

### Tests for User Story 2
- [x] T012 [P] [US2] Criar testes unitários para a fórmula de cálculo do saldo projetado em `tests/unit/use_cases/test_dashboard_projections.py`

### Implementation for User Story 2
- [x] T013 [US2] Implementar caso de uso de cálculo de projeções financeiras (`GetDashboardProjectionsUseCase`) em `src/contas/application/use_cases/transactions.py` e registrar no container de dependências em `src/contas/application/container.py`
- [x] T014 [US2] Adicionar método `get_dashboard_projections` em `src/contas/ui/services.py`
- [x] T015 [US2] Integrar cálculo de saldo projetado nas métricas de "Patrimônio Total" e "Saldos por Conta" em `src/contas/ui/app.py`

**Checkpoint**: Dashboard exibe com precisão matemática tanto o Saldo Atual quanto o Saldo Projetado.

---

## Phase 5: User Story 3 - Alternador Rápido de Visão e Destaques no Dashboard (Priority: P3)

**Goal**: Adicionar controle visual no Dashboard para alternar entre "Saldo Atual" e "Saldo Projetado", com alerta caso o saldo projetado fique negativo.

**Independent Test**: Simular conta com projeção negativa e verificar se o card exibe destaque de alerta visual na interface.

### Implementation for User Story 3
- [x] T016 [US3] Implementar controle seletor horizontal (`st.radio`) no topo da seção de saldos do Dashboard em `src/contas/ui/app.py`
- [x] T017 [US3] Adicionar formatação condicional e indicador de alerta caso o saldo projetado seja menor que zero em `src/contas/ui/app.py`

**Checkpoint**: Todas as user stories implementadas e integradas de forma reativa.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Qualidade, padronização e garantia de conformidade com a Constituição do Contas

- [x] T018 [P] Executar linter e formatação estrita com `.venv/bin/ruff check --fix .` e `.venv/bin/ruff format .`
- [x] T019 Executar a suíte completa de testes com `pytest` cobrindo todos os novos casos de uso
- [x] T020 [P] Validar o fluxo de ponta a ponta seguindo o roteiro do [quickstart.md](quickstart.md)

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Inicializa schemas independentes.
- **Phase 2 (Foundational)**: Bloqueia todas as User Stories; estende repositórios de dados.
- **Phase 3 (User Story 1 - P1 MVP)**: Depende da Phase 2. Entrega valor imediato ao usuário.
- **Phase 4 (User Story 2 - P2)**: Depende da Phase 2. Pode ser desenvolvida em paralelo ou logo após a US1.
- **Phase 5 (User Story 3 - P3)**: Depende da conclusão da US2 (aprimoramento de UI).
- **Phase 6 (Polish)**: Depende de todas as histórias concluídas.

### Parallel Opportunities
- T002 e T003 podem ser executados em paralelo.
- T007 (testes US1) e T012 (testes US2) podem ser escritos em paralelo.
- T009 (MCP tool) e T010 (UIService) podem ser implementados em paralelo.

---

## Implementation Strategy

### MVP First (User Story 1)
1. Completar Setup (T001 - T003).
2. Completar Foundational (T004 - T006).
3. Implementar User Story 1 (T007 - T011).
4. **Validar MVP**: Testar o extrato com filtros "Apenas Pendentes", "Apenas Quitadas" e "Todas".

### Entrega Incremental
1. MVP entregue com o extrato operacional.
2. Implementar User Story 2 (T012 - T015) para habilitar o cálculo de saldo projetado.
3. Implementar User Story 3 (T016 - T017) para refinar a experiência do Dashboard com alternador e alertas.
4. Finalizar com linter, formatação e bateria de testes (T018 - T020).
