# Pesquisa Técnica: Banco de Dados (SQLModel + Alembic + psycopg3)

**Feature**: `001-core-infra-mcp`
**Tecnologias**: `sqlmodel >= 0.0.21`, `alembic >= 1.13`, `psycopg[binary] >= 3.1`
**Data**: 2026-09-19

---

## Dialeto Unificado: `postgresql+psycopg://`

**Decisão**: Usar o driver `psycopg3` com o dialeto `postgresql+psycopg://` do SQLAlchemy 2.0.

**Justificativa**: Um único dialeto funciona tanto com `create_engine()` (síncrono — usado pelo Alembic nas migrações) quanto com `create_async_engine()` (assíncrono — usado pelo servidor MCP em runtime). Elimina a necessidade de dois drivers distintos.

```python
DATABASE_URL = "postgresql+psycopg://username:password@hostname:5432/database"
```

Para credenciais com caracteres especiais, usar `URL.create()`:

```python
from sqlalchemy.engine import URL

url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=os.getenv("POSTGRES_DB"),
)
```

---

## Valores Monetários: `Decimal` + `NUMERIC(14, 2)`

**Decisão**: `sa_type=Numeric(precision=14, scale=2)` + `Field(max_digits=14, decimal_places=2)`

**Justificativa**: Evita qualquer divergência de ponto flutuante. `NUMERIC(14,2)` suporta até R$ 999.999.999.999,99. Proibição de `float` é princípio inegociável da Constituição (Princípio II).

```python
from decimal import Decimal
from sqlmodel import SQLModel, Field
from sqlalchemy import Numeric

class TransactionBase(SQLModel):
    amount: Decimal = Field(
        sa_type=Numeric(precision=14, scale=2),
        max_digits=14,
        decimal_places=2,
        nullable=False,
    )
```

> **Por que `sa_type` e não `sa_column`?**
> `sa_type` permite que o SQLModel gerencie o objeto `Column`, evitando o erro `ArgumentError: Column object already assigned to Table` em herança de classes base. Padrão recomendado no SQLModel moderno.

---

## Enums com `StrEnum` + Native PostgreSQL Enum

**Decisão**: `class TransactionType(StrEnum)` com `sa.Enum(..., native_enum=True)` no banco.

**Justificativa**: `StrEnum` (Python 3.11+) garante serialização JSON limpa e validação automática no Pydantic v2. Native enum no PostgreSQL impõe restrição de domínio no banco.

```python
from enum import StrEnum
import sqlalchemy as sa
from sqlmodel import SQLModel, Field
from sqlalchemy import Column

class TransactionType(StrEnum):
    INCOME   = "income"
    EXPENSE  = "expense"
    TRANSFER = "transfer"

class Transaction(SQLModel, table=True):
    __tablename__ = "transaction"
    transaction_type: TransactionType = Field(
        sa_column=Column(
            sa.Enum(TransactionType, name="transaction_type_enum", native_enum=True),
            nullable=False,
        )
    )
```

> **Atenção para Alembic**: `ALTER TYPE ... ADD VALUE` no PostgreSQL não é transacional. Novos valores de enum devem ser adicionados fora de blocos de transação. Avaliar `native_enum=False` se expansão frequente de enums for prevista.

---

## Session Factory Assíncrona

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from contextlib import asynccontextmanager

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,   # detecta conexões mortas
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # OBRIGATÓRIO em async: previne MissingGreenlet
)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

> **`expire_on_commit=False` é obrigatório** em contexto assíncrono. Sem isso, acessar atributos do modelo após o commit gera `MissingGreenlet`.

---

## Alembic com Template Assíncrono

**Inicialização**:
```bash
uv run alembic init -t async migrations
```

**Configurações críticas no `env.py`**:

```python
from sqlmodel import SQLModel
from contas.models import Account, Category, Transaction  # importar TODOS os modelos

target_metadata = SQLModel.metadata

# No context.configure():
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    compare_type=True,           # OBRIGATÓRIO: detecta mudanças em Numeric e Enum
    compare_server_default=True, # detecta mudanças em defaults do banco
)
```

> **`compare_type=True` é obrigatório** — sem isso, o Alembic ignora mudanças de precisão/escala em `Numeric(14, 2)` e mudanças de valores em `Enum`.

**`DATABASE_URL` via variável de ambiente**:
```python
# No topo do env.py, antes de target_metadata:
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
```

---

## Integridade Referencial

**Regra financeira**: Nunca apagar silenciosamente histórico contábil. `ondelete="RESTRICT"` em todas as FKs de `Transaction`.

```python
class Transaction(SQLModel, table=True):
    source_account_id: uuid.UUID = Field(
        foreign_key="account.id",
        ondelete="RESTRICT",
        nullable=False,
        index=True,
    )
    destination_account_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="account.id",
        ondelete="RESTRICT",
        nullable=True,
        index=True,
    )
    category_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="category.id",
        ondelete="RESTRICT",
        nullable=True,
        index=True,
    )
```

**Relacionamentos com múltiplas FKs para a mesma tabela**:

`Transaction` tem `source_account_id` e `destination_account_id` apontando para `Account`. Exige desambiguação explícita para evitar `AmbiguousForeignKeysError`:

```python
# Em Account:
outgoing_transactions: list["Transaction"] = Relationship(
    back_populates="source_account",
    sa_relationship_kwargs={
        "foreign_keys": "Transaction.source_account_id",
        "passive_deletes": True,
    },
)

# Em Transaction:
source_account: Account = Relationship(
    back_populates="outgoing_transactions",
    sa_relationship_kwargs={"foreign_keys": [source_account_id]},
)
```

`passive_deletes=True` — delega o enforcement de FK ao PostgreSQL, evitando queries desnecessárias do ORM.

---

## Soft Delete

`Account` e `Category` usam `is_active: bool = Field(default=True)` como estratégia de "remoção" para registros que já possuem transações associadas (não é possível deletar por causa do `RESTRICT`).

