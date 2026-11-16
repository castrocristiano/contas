# Tasks: Remoção do o3-mini e Carregamento Dinâmico de Modelos OpenAI (024-dynamic-llm-models)

**Input**: Design documents from `/specs/024-dynamic-llm-models/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/models_contracts.md](contracts/models_contracts.md)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Tarefa paralelizada
- **[Story]**: Mapeamento para as User Stories do [spec.md](spec.md) (`[US1]`, `[US2]`, `[US3]`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Definição de constantes e configuração base

- [x] T001 Atualizar `invoice_model` padrão para `"gpt-4o"` em `src/contas/config.py`
- [x] T002 [P] Atualizar referências a `o3-mini` para `gpt-4o` em `README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Módulo central de listagem e filtragem de modelos OpenAI

- [x] T003 Criar o módulo `src/contas/services/openai_models.py` com `DEFAULT_FALLBACK_MODELS`, função de filtragem e cache TTL
- [x] T004 Implementar `get_available_openai_models` com suporte a `client.models.list()`, fallback resiliente e `force_refresh` em `src/contas/services/openai_models.py`

---

## Phase 3: User Story 1 - Remoção do Modelo Deprecado o3-mini (Priority: P1) 🎯 MVP

**Goal**: Eliminar `o3-mini` de todo o sistema e estabelecer `gpt-4o` como novo padrão estável.

### Tests for User Story 1
- [x] T005 [P] [US1] Atualizar testes em `tests/unit/test_invoice_parser.py` para validar `gpt-4o` em vez de `o3-mini`

### Implementation for User Story 1
- [x] T006 [US1] Remover referências a `o3-mini` em `src/contas/services/invoice_parser.py`
- [x] T007 [US1] Remover referências a `o3-mini` nas opções de modelos e textos de ajuda em `src/contas/ui/app.py`

---

## Phase 4: User Story 2 - Carregamento Dinâmico de Modelos da Conta OpenAI (Priority: P2)

**Goal**: Consultar dinamicamente os modelos ativos da conta OpenAI com filtragem e cache.

### Tests for User Story 2
- [x] T008 [P] [US2] Criar testes unitários para `get_available_openai_models` (sucesso, filtro, fallback e cache) em `tests/unit/test_openai_models.py`

### Implementation for User Story 2
- [x] T009 [US2] Integrar `get_available_openai_models` no seletor de modelos de IA da tela de faturas em `src/contas/ui/app.py`

---

## Phase 5: User Story 3 - Botão de Atualização Manual de Modelos na Interface (Priority: P3)

**Goal**: Permitir forçar atualização da lista de modelos da OpenAI com 1 clique na UI.

### Implementation for User Story 3
- [x] T010 [US3] Adicionar botão de refresh com ícone "🔄" ao lado do seletor de modelo em `src/contas/ui/app.py`
- [x] T011 [US3] Adicionar feedback visual com `st.toast` ao atualizar modelos em `src/contas/ui/app.py`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Qualidade de código e validação de conformidade com a Constituição do Contas

- [x] T012 [P] Executar linter e formatação estrita com `.venv/bin/ruff check --fix .` e `.venv/bin/ruff format .`
- [x] T013 Executar a suíte de testes unitários com `pytest` garantindo 100% de aprovação
- [x] T014 [P] Validar o fluxo de ponta a ponta seguindo o roteiro do [quickstart.md](quickstart.md)
