# Implementation Plan: Filtros de Quitação e Saldo Projetado no Dashboard e Extratos (023-settlement-filters)

**Branch**: `feature/023-settlement-filters` | **Date**: 2026-11-14 | **Spec**: [specs/023-settlement-filters/spec.md](spec.md)

**Input**: Feature specification from `/specs/023-settlement-filters/spec.md`

---

## Summary

Implementar filtros dinâmicos de quitação (`cleared` vs `pending`) no Extrato de Movimentações e uma visão de Saldo Atual versus Saldo Projetado no Dashboard.

No Extrato, o usuário poderá isolar rapidamente transações pendentes (ocultando as já quitadas) ou visualizar apenas o histórico realizado, com recálculo determinístico e exato dos resumos financeiros. No Dashboard, o usuário terá acesso ao cálculo e alternância entre o Saldo Atual (realizado em conta) e o Saldo Projetado (saldo atual + receitas pendentes - despesas e transferências pendentes do período), garantindo clareza sobre os recursos efetivamente disponíveis para honrar compromissos futuros.

---

## Technical Context

**Language/Version**: Python 3.12+ gerenciado via `uv`.

**Primary Dependencies**: 
- Framework de UI: Streamlit 1.39+.
- Protocolo & Validação: Python MCP SDK, Pydantic v2, SQLModel / SQLAlchemy 2.0.
- Manipulação Numérica: Módulo nativo `decimal` (`Decimal`, `ROUND_HALF_UP`).

**Storage**: PostgreSQL 16 (tabelas `account` e `transaction`), consultas com índices existentes em `(source_account_id, transaction_date)`, `(status)` e `(user_id)`.

**Testing**: `pytest`, `pytest-asyncio` para testes unitários de casos de uso e integração de repositórios.

**Target Platform**: Linux (containers Podman/Docker e execução nativa) e web browser.

**Project Type**: Clean Architecture Web App (Streamlit) & MCP Server.

**Performance Goals**:
- Resposta das consultas de extrato filtrado < 50ms para 500 registros.
- Renderização e recálculo da projeção do Dashboard sem degradação perceptível na UI.

**Constraints**:
- Não introduzir representação `float` em cálculos financeiros (Princípio II da Constituição).
- Código-fonte e identificadores estritamente em inglês (Princípio VI).
- Manter 100% de compatibilidade retroativa com chamadas existentes ao MCP `get_statement`.

**Scale/Scope**:
- Modificação em schemas (`GetStatementInput`), casos de uso (`GetStatementUseCase`), repositório de transações e views da UI (`app.py`, `services.py`).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio Constitucional | Avaliação | Status |
|:---|:---|:---:|
| **I. Simplicidade e YAGNI** | Reutiliza as colunas e entidades existentes (`TransactionStatus`, `Account.balance`). Sem triggers ou tabelas intermediárias complexas. Projeção calculada sob demanda via agregação pura. | **APROVADO** |
| **II. Integridade e Precisão Financeira** | Todo cálculo de saldo projetado e somas de extrato utilizam `Decimal("0.00")`. O saldo real em `Account.balance` permanece inalterado até a quitação explícita. | **APROVADO** |
| **III. Interface MCP Declarativa e Autônoma** | O parâmetro `status_filter` é tipado via schema Pydantic e documentado na tool `get_statement`. | **APROVADO** |
| **IV. Integração com IA Segura e Estruturada** | Nenhuma dependência desestruturada de IA é introduzida. Apenas filtros e agregações matemáticas determinísticas. | **APROVADO** |
| **V. Conteinerização e Portabilidade com Podman** | Totalmente compatível com a stack existente em `podman-compose`. Nenhuma nova porta ou serviço externo é necessário. | **APROVADO** |
| **VI. Idioma: Documentação em PT-BR e Código em EN-US** | Especificações, planos e UI em PT-BR; todo o código Python, testes, variáveis, schemas e métodos escritos em Inglês (EN-US). | **APROVADO** |

---

## Project Structure

### Documentation (this feature)

```text
specs/023-settlement-filters/
├── spec.md              # Especificação de requisitos da funcionalidade
├── plan.md              # Plano mestre de implementação (este documento)
├── research.md          # Decisões arquiteturais e alternativas avaliadas
├── data-model.md        # Modelos de dados e transições de estado
├── quickstart.md        # Guia passo a passo de validação
├── contracts/
│   └── statement_and_dashboard_contracts.md # Contratos MCP e UI
└── checklists/
    └── requirements.md  # Validação de conformidade dos requisitos
```

### Source Code Layout

```text
src/contas/
├── application/
│   ├── ports/
│   │   └── repositories.py          # Adiciona suporte a status_filter em list_by_account
│   └── use_cases/
│       └── transactions.py          # Atualiza GetStatementUseCase e implementa projeções
├── infrastructure/
│   └── repositories/
│       └── transaction.py           # Filtro SQL por status em list_by_account
├── schemas/
│   ├── account.py                   # Schemas de projeção de saldo
│   └── transaction.py               # StatementStatusFilter e status_filter em GetStatementInput
├── server.py                        # Atualização da tool MCP get_statement
└── ui/
    ├── app.py                       # Interface do Dashboard (projeções) e Extrato (seletor)
    └── services.py                  # Integração com UIService

tests/
├── unit/
│   └── use_cases/
│       ├── test_get_statement_status_filter.py # Testes do filtro no extrato
│       └── test_dashboard_projections.py       # Testes da fórmula de projeção
```

---

## Complexity Tracking

> Nenhuma violação constitucional detectada. Sem necessidade de exceções de complexidade.

| Item | Avaliação | Justificativa |
|:---|:---|:---|
| Nova dependência externa | Nenhuma | Usando stdlib `Decimal` e stack existente |
| Novas tabelas de banco | Nenhuma | Aproveitamento integral do schema relacional atual |
| Migrações de banco (Alembic) | Não necessária | As colunas `status` e relacionamentos já existem |
