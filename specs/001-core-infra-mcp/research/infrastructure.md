# Pesquisa Técnica: Infraestrutura (Podman Compose + PostgreSQL)

**Feature**: `001-core-infra-mcp`
**Tecnologias**: `podman-compose`, PostgreSQL 16 Alpine, Podman Rootless
**Data**: 2026-09-19

---

## `podman-compose.yml` Completo

```yaml
version: "3.8"

services:
  db:
    image: docker.io/library/postgres:16-alpine
    container_name: contas-db
    restart: unless-stopped
    env_file:
      - .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-contas}
      POSTGRES_USER: ${POSTGRES_USER:-contas}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-contas}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data:Z
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER:-contas} -d $${POSTGRES_DB:-contas} -h localhost"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - contas_network

  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: contas-mcp
    restart: unless-stopped
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-contas}:${POSTGRES_PASSWORD:-contas}@db:5432/${POSTGRES_DB:-contas}
      PYTHONUNBUFFERED: "1"
    depends_on:
      db:
        condition: service_healthy
    stdin_open: true
    tty: true
    networks:
      - contas_network

volumes:
  postgres_data:
    driver: local

networks:
  contas_network:
    driver: bridge
```

---

## Variáveis de Ambiente via `.env`

O `podman-compose` opera com dois mecanismos:

1. **Interpolação no arquivo Compose** (`${VAR}`): O compose lê `.env` na raiz e substitui as referências antes de criar os containers.
2. **Injeção no container** (`env_file: [.env]`): Passa os valores diretamente para o processo dentro do container.

```bash
# .env (não versionar — adicionar ao .gitignore)
POSTGRES_DB=contas
POSTGRES_USER=contas
POSTGRES_PASSWORD=contas_dev_password

DATABASE_URL=postgresql+psycopg://contas:contas_dev_password@localhost:5432/contas
OPENAI_API_KEY=sk-...
```

> **`$$` no healthcheck**: Ao usar variáveis dentro de `CMD-SHELL`, usar `$$` para escapar — impede que o Compose expanda a variável localmente antes de repassá-la ao shell do container.

---

## Volume Nomeado vs Bind Mount (Rootless)

**Decisão**: Volume nomeado `postgres_data` gerenciado pelo Podman.

**Por quê não usar bind mount** (`./data:/var/lib/postgresql/data`):
- Em Podman rootless, o processo PostgreSQL roda como UID 999 dentro do container
- O diretório no host pertence ao UID 1000 do usuário host
- O mapeamento de user namespace torna UID 999 do container diferente do UID 1000 do host
- Resultado: `Permission Denied` durante o `initdb`

**Vantagem do volume nomeado**:
- Armazenado em `~/.local/share/containers/storage/volumes/`
- Podman ajusta automaticamente os UID/GID via user namespace
- Zero problemas de permissão

---

## Flag SELinux `:Z`

Necessária em Fedora, RHEL, Rocky, CentOS com SELinux ativo:

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data:Z
```

O sufixo `:Z` instrui o Podman a reetiquetar o volume com `container_file_t` (uso privado por um único container). Sem essa flag, o SELinux bloqueará o acesso ao volume.

---

## Healthcheck do PostgreSQL

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER:-contas} -d $${POSTGRES_DB:-contas} -h localhost"]
  interval: 5s
  timeout: 5s
  retries: 5
  start_period: 10s
```

- `pg_isready` — utilitário nativo da imagem `postgres:16-alpine`
- `start_period: 10s` — período de graça durante `initdb` e restart inicial
- `retries: 5` × `interval: 5s` — até 25 segundos de tentativas antes de declarar `unhealthy`

---

## Aguardar PostgreSQL antes de Iniciar o Python

```yaml
depends_on:
  db:
    condition: service_healthy
```

**Resiliência adicional na aplicação Python** (recomendado, pois o `podman-compose` pode ter inconsistências de timing):

```sh
# entrypoint.sh
until pg_isready -h db -p 5432 -U contas; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done
exec uv run python -m contas
```

Ou retry com backoff exponencial na inicialização da sessão assíncrona (`pool_pre_ping=True` no SQLAlchemy já ajuda em reconexões).

---

## Rede Customizada: Obrigatória no Podman

**Decisão**: Rede explícita `contas_network` com `driver: bridge`.

**Justificativa**: Em Podman rootless, o DNS por nome de serviço (`db`, `mcp-server`) **não é garantido** na rede padrão. Com rede customizada explícita, o Podman configura DNS interno corretamente via `netavark`.

Sem isso, `DATABASE_URL=...@db:5432/...` falha com `Name or service not known`.

---

## Diferenças Relevantes: Podman vs Docker

| Aspecto | Docker Compose | Podman Compose (Rootless) |
| :--- | :--- | :--- |
| Daemon | `dockerd` (root) | Daemonless, sem daemon central |
| DNS entre serviços | Automático na bridge default | Requer rede customizada explícita |
| Bind mounts | UID direto | User namespace — usar named volumes |
| SELinux | Bypass | Ativo — precisa de `:Z` |
| Acesso ao host | `host.docker.internal` | `host.containers.internal` |
| Engine | `docker compose` (Go, v2) | Script Python (wrapper de `podman run`) |

> Para maior compatibilidade com Docker Compose v2, é possível usar o plugin `podman compose` apontando para o socket de usuário (`podman.socket`). Para este projeto, `podman-compose` (script Python) é suficiente.

