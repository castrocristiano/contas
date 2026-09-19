# Pesquisa Técnica — Índice

**Feature**: `001-core-infra-mcp`
**Data**: 2026-09-19
**Status**: Completa

A pesquisa foi organizada por tecnologia em arquivos separados:

| Arquivo | Tecnologias | Tópicos Cobertos |
| :--- | :--- | :--- |
| [`research/mcp-sdk.md`](./research/mcp-sdk.md) | `mcp >= 2.2.0`, Pydantic v2 | `MCPServer`, `@mcp.tool()`, transporte stdio, registro modular, validação Pydantic |
| [`research/database.md`](./research/database.md) | SQLModel, Alembic, psycopg3 | `Decimal`/`NUMERIC(14,2)`, `StrEnum`, session factory async, Alembic async, integridade FK |
| [`research/infrastructure.md`](./research/infrastructure.md) | Podman Compose, PostgreSQL 16 | `podman-compose.yml`, volumes nomeados, healthcheck, rede customizada, diferenças vs Docker |

---

## Resumo das Decisões

| Decisão | Escolha | Alternativa Descartada |
| :--- | :--- | :--- |
| Classe MCP | `MCPServer` (SDK 2.x) | API low-level `Server` — complexidade desnecessária |
| Transporte MCP | `stdio` | HTTP/SSE — não necessário para uso local no MVP |
| Schema nas tools | `BaseModel` Pydantic dedicado por tool | Argumentos `Annotated` inline — menos legível em payloads complexos |
| Valores monetários | `Decimal` + `NUMERIC(14,2)` | `float` — proibido pela Constituição |
| Enum Python | `StrEnum` + native PostgreSQL enum | `str` puro — sem validação de domínio no banco |
| Driver PostgreSQL | `psycopg3` (`postgresql+psycopg://`) | `asyncpg` (só async) ou `psycopg2` (só sync) |
| Volume PostgreSQL | Named volume `postgres_data` | Bind mount — quebra em Podman rootless |
| Rede Podman | Customizada explícita `contas_network` | Rede default — DNS não garantido no Podman |
