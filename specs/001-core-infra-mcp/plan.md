# Plano de Implementação: Infraestrutura Base e Servidor MCP de Finanças

**Branch**: `001-core-infra-mcp` | **Data**: 2026-09-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification em [`specs/001-core-infra-mcp/spec.md`](./spec.md)

---

## Resumo

Construir a infraestrutura completa do sistema **Contas**: banco de dados PostgreSQL 16 orquestrado com `podman-compose` em modo rootless, modelos SQLModel com precisão decimal financeira e migrações Alembic versionadas, e um servidor MCP em Python expondo 6 ferramentas (`create_account`, `list_accounts`, `record_transaction`, `get_statement`, `get_financial_summary`, `health_check`) com validação Pydantic v2 estrita.

---

## Contexto Técnico

**Language/Version**: Python 3.12+ gerenciado por `uv`

**Primary Dependencies**:
- `mcp[cli] >= 2.2.0` — SDK oficial MCP, classe `MCPServer` (alta nível, substituiu `FastMCP`)
- `pydantic >= 2.0` — validação de schemas das tools MCP e I/O
- `sqlmodel >= 0.0.21` — ORM + schemas Pydantic unificados sobre SQLAlchemy 2.0
- `alembic >= 1.13` — migrações versionadas do schema do banco
- `psycopg[binary] >= 3.1` — driver PostgreSQL 3, dialeto `postgresql+psycopg://` unificado (sync + async)
- `python-dotenv >= 1.0` — leitura de `.env` em desenvolvimento
- `openai >= 1.0` — integração futura com API OpenAI (sem uso nesta feature)

**Dev Dependencies**: `pytest >= 9.1.1`, `ruff >= 0.16.8`

**Storage**: PostgreSQL 16 via `podman-compose` rootless com volume nomeado `postgres_data`

**Testing**: `pytest` com nomenclatura EN-US; testes unitários de schemas e modelos; testes de integração das tools MCP

**Target Platform**: Linux, ambiente containerizado local (Podman rootless)

**Project Type**: Servidor MCP (serviço local via `stdio`) + CLI (`uv run contas`)

**Performance Goals**: Operações de leitura/escrita < 1 segundo em ambiente local (CS-002)

**Constraints**:
- Valores monetários: `Decimal` + `NUMERIC(14,2)` — zero ponto flutuante (CS-001)
- Credenciais nunca versionadas — exclusivamente via `.env` (Constituição V)
- Código-fonte exclusivamente em inglês (Constituição VI)

**Scale/Scope**: Uso doméstico/unifamiliar — single user, sem necessidade de autenticação ou multi-tenancy nesta feature

---

## Constitution Check

*GATE: Verificação pré-pesquisa. Re-verificado pós-design.*

| Princípio | Status | Evidência |
| :--- | :---: | :--- |
| **I. Simplicidade/YAGNI** | ✅ | Sem camadas extras. Sem Repository pattern. Acesso direto via session nas tools. |
| **II. Precisão Financeira** | ✅ | `Decimal` + `NUMERIC(14,2)` em todos os campos monetários. Zero `float`. |
| **III. Interface MCP Declarativa** | ✅ | 6 tools com schemas Pydantic v2 estrito. `extra="forbid"`. Descrições em todos os campos. |
| **IV. IA Segura e Estruturada** | ✅ | IA não persiste dados diretamente. Toda persistência passa pela validação de schema. |
| **V. Podman Rootless** | ✅ | `podman-compose` com volume nomeado, rede customizada, SELinux `:Z`, sem bind mounts problemáticos. |
| **VI. Idioma PT-BR / EN-US** | ✅ | Código, modelos, schemas, tabelas em EN-US. Docs em PT-BR. |

**Resultado**: ✅ Sem violações. Nenhuma justificativa de complexidade necessária.

---

## Estrutura do Projeto

### Documentação desta feature

```text
specs/001-core-infra-mcp/
├── plan.md              # Este arquivo
├── research.md          # Pesquisa técnica consolidada
├── data-model.md        # Entidades, campos, enums, relacionamentos
├── quickstart.md        # Guia de validação end-to-end
├── contracts/
│   └── mcp-tools.md     # Schemas JSON de input/output das 6 tools
└── tasks.md             # Gerado por /speckit-tasks (próximo passo)
```

### Código-fonte (raiz do repositório)

```text
src/contas/
├── __init__.py           # Entry point existente (manter main())
├── __main__.py           # [NEW] uv run python -m contas → servidor MCP
├── server.py             # [NEW] MCPServer + registro modular de tools
├── config.py             # [NEW] Settings com pydantic-settings + .env
├── db/
│   ├── __init__.py       # [NEW]
│   ├── engine.py         # [NEW] create_async_engine + session factory
│   └── session.py        # [NEW] get_session context manager assíncrono
├── models/
│   ├── __init__.py       # [NEW]
│   ├── account.py        # [NEW] SQLModel table=True Account
│   ├── category.py       # [NEW] SQLModel table=True Category
│   └── transaction.py    # [NEW] SQLModel table=True Transaction
├── schemas/
│   ├── __init__.py       # [NEW]
│   ├── account.py        # [NEW] Pydantic I/O schemas (CreateAccountInput, AccountResponse)
│   ├── category.py       # [NEW] Pydantic I/O schemas para Category
│   └── transaction.py    # [NEW] Pydantic I/O schemas para Transaction
└── tools/
    ├── __init__.py       # [NEW]
    ├── accounts.py       # [NEW] create_account, list_accounts
    ├── transactions.py   # [NEW] record_transaction, get_statement, get_financial_summary
    └── health.py         # [NEW] health_check

migrations/               # [NEW] Alembic template async
├── env.py
├── script.py.mako
├── alembic.ini
└── versions/

tests/
├── test_initial.py       # Existente (baseline — manter)
├── unit/
│   ├── __init__.py       # [NEW]
│   ├── test_schemas.py   # [NEW] Validação Pydantic dos schemas das tools
│   └── test_models.py    # [NEW] Comportamento dos enums e regras de domínio
└── integration/
    ├── __init__.py       # [NEW]
    └── test_tools.py     # [NEW] Tools MCP com banco real (pytest-anyio)

podman-compose.yml        # [NEW] PostgreSQL 16 + rede customizada + healthcheck
.env.example              # [NEW] Referência de variáveis de ambiente (sem valores reais)
```

**Decisão de estrutura**: Projeto único (Option 1). Sem frontend. Sem multi-package. Toda lógica em `src/contas/`.

---

## Complexity Tracking

> Nenhuma violação da Constituição identificada. Seção não aplicável.

---

## Plano de Verificação

### Testes Automatizados
```bash
# Todos os testes
uv run pytest -v

# Linting e formatação
uv run ruff check .
uv run ruff format --check .
```

### Validação Manual
Ver guia completo em [`quickstart.md`](./quickstart.md). Pontos críticos:
1. `podman-compose up -d` → PostgreSQL em estado `healthy`
2. `uv run alembic upgrade head` → schema criado sem erros
3. `uv run mcp dev src/contas/server.py` → MCP Inspector abre em `http://localhost:6274`
4. Criar conta + registrar despesa + verificar saldo atualizado (`1500.00 - 35.50 = 1464.50`)
5. Tool `health_check` retorna `status: "healthy"`
6. Lançamentos inválidos (valor zero, conta inexistente) retornam erros com código estruturado
