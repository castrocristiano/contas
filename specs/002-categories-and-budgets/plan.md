# Implementation Plan: Gestão de Categorias e Orçamentos (002-categories-and-budgets)

**Branch**: `feature/002-categories-and-budgets` | **Date**: 2026-09-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-categories-and-budgets/spec.md`

## Summary

Implementação da gestão completa de categorias financeiras (`income` / `expense`), criação da entidade `Budget` para estipular tetos de gastos mensais e desenvolvimento de ferramentas MCP para cadastro, listagem e acompanhamento de execução orçamentária com cálculo de consumo e alertas de limites excedidos.

## Technical Context

**Language/Version**: Python 3.12+ gerenciado pelo `uv`
**Primary Dependencies**: `sqlmodel>=0.0.21`, `alembic>=1.13`, `mcp[cli]>=2.2.0`, `pydantic>=2.0`, `psycopg[binary]>=3.1`
**Storage**: PostgreSQL 16+ via SQLModel / async engine
**Testing**: `pytest` com asserções assíncronas
**Target Platform**: Linux / Containers via `podman-compose`
**Project Type**: Servidor MCP / API de linha de comando
**Performance Goals**: Tempo de resposta de queries orçamentárias < 100ms
**Constraints**: Uso exclusivo de `Decimal` e `NUMERIC(14,2)` para valores monetários (Princípio II da Constituição)
**Scale/Scope**: Controle financeiro doméstico / multi-categoria

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Princípio I (Simplicidade e YAGNI)**: Aprovado. Apenas o modelo `Budget` mensal e consultas diretas ao banco, sem agendadores em background desnecessários.
- **Princípio II (Integridade e Precisão Financeira)**: Aprovado. `amount` em `Decimal` e banco em `NUMERIC(14,2)`. Proibição estrita de float respeitada.
- **Princípio III (Interface MCP Declarativa e Autônoma)**: Aprovado. Ferramentas `create_category`, `list_categories`, `set_budget` e `get_budget_status` com schemas Pydantic estritos.
- **Princípio V (Conteinerização e Portabilidade com Podman)**: Aprovado. Utiliza o banco de dados provisionado no container existente.
- **Princípio VI (Idioma: Documentação em PT-BR e Código em EN-US)**: Aprovado. Specs e planos em PT-BR; código, modelos e testes em EN-US.

## Project Structure

### Documentation (this feature)

```text
specs/002-categories-and-budgets/
├── spec.md              # Especificação de requisitos e cenários
├── checklists/
│   └── requirements.md  # Checklist de qualidade da especificação
├── plan.md              # Este plano de implementação
├── research.md          # Pesquisa técnica e decisões de arquitetura
├── data-model.md        # Modelo de dados da entidade Budget e relacionamentos
├── contracts/
│   └── mcp-tools.md     # Contratos e schemas das ferramentas MCP
└── quickstart.md        # Guia de validação ponta a ponta
```

### Source Code (repository root)

```text
src/contas/
├── models/
│   ├── category.py      # Modelo Category (já existente)
│   ├── budget.py        # [NOVO] Modelo Budget(SQLModel, table=True)
│   └── __init__.py      # Exportações de modelos
├── schemas/
│   ├── category.py      # [NOVO] Schemas de Category (CreateCategoryInput, etc.)
│   └── budget.py        # [NOVO] Schemas de Budget (SetBudgetInput, BudgetStatusResponse, etc.)
├── tools/
│   ├── categories.py    # [NOVO] Tools create_category, list_categories
│   ├── budgets.py       # [NOVO] Tools set_budget, get_budget_status
│   └── errors.py        # Atualização com novas exceções (ex: BudgetNotFoundError)
└── server.py            # Registro das novas ferramentas no MCPServer

migrations/
└── versions/            # Nova migração Alembic para a tabela budget
```

**Structure Decision**: Segue o padrão modular do projeto implementado na feature `001`, isolando models, schemas Pydantic e handlers MCP.

## Complexity Tracking

*Nenhuma violação identificada em relação à Constituição.*
