# 🚀 05. Guia de Instalação e Deploy

O **Contas** foi projetado para execução simples tanto em ambiente de desenvolvimento quanto em produção conteinerizada com **PostgreSQL 16**, **Keycloak 26** e **Streamlit**.

---

## 📦 Opção 1: Execução com Docker / Podman Compose (Recomendado)

Esta opção sobe toda a infraestrutura isolada em 3 containers orquestrados:
- **`contas-db`**: PostgreSQL 16 (porta `5432`, schemas `public` e `keycloak`).
- **`contas-keycloak`**: Keycloak 26 (porta `8180` mapeada para `8080` interna, com importação automática do realm `contas`).
- **`contas-app`**: Aplicação Streamlit + Servidor MCP (porta `8501`).

### Passo 1: Clonar o projeto e configurar `.env`
```bash
git clone git@github.com:castrocristiano/contas.git
cd contas
cp .env.example .env
```
Edite o arquivo `.env` para informar sua chave `OPENAI_API_KEY` e ajustar `KEYCLOAK_SERVER_URL` / `KEYCLOAK_REDIRECT_URI` caso esteja rodando em um servidor na rede local (ex: `http://192.168.1.20:8180` e `http://192.168.1.20:8501`).

### Passo 2: Subir os containers
```bash
# Com Docker:
docker compose up --build -d

# Ou com Podman:
podman-compose up --build -d
```

O container da aplicação executa automaticamente as migrações do banco com Alembic na inicialização (`entrypoint.sh`).

- 🌐 **Aplicação Contas:** **`http://localhost:8501`**
- 🔐 **Keycloak Admin Console:** **`http://localhost:8180`** *(usuário/senha padrão: `admin` / `admin`)*

---

## 🔄 Deploy e Atualização do Servidor Remoto (`update_remote.sh`)

Para atualizar o servidor de produção (`192.168.1.20`) com a última Release gerada pelo GitHub Actions na branch `main`:

```bash
./update_remote.sh
```

O script `update_remote.sh` realiza automaticamente:
1. Consulta na API do GitHub a última tag/release publicada (`releases/latest`).
2. Compara com a versão instalada em `/home/cristiano/contas/.current_release_version` (ou força atualização com `FORCE=1 ./update_remote.sh`).
3. Faz backup do `.env` remoto, baixa e extrai o tarball da nova release e restaura o `.env`.
4. Reconstrói e reinicia os containers via `podman-compose` / `docker-compose`.

---

## 💻 Opção 2: Execução Local Nativa com `uv`

Ideal para desenvolvimento ativo e depuração de código:

### 1. Pré-requisitos
- Python 3.12 ou superior
- [uv](https://github.com/astral-sh/uv) (gerenciador de dependências)

### 2. Instalação de Dependências
```bash
uv sync
```

### 3. Iniciar o Banco PostgreSQL e o Keycloak
```bash
docker compose up db keycloak -d  # ou: podman-compose up db keycloak -d
```

### 4. Executar Migrações do Banco
```bash
uv run alembic upgrade head
```

### 5. Iniciar a Aplicação
```bash
uv run streamlit run src/contas/ui/app.py
```

---

## 🧪 Suíte de Testes, Qualidade & CI/CD (`contas-ci`)

A validação de código, testes e análise de qualidade são orquestrados pela ferramenta CLI em Go (`contas-ci`), executável nativamente ou de forma 100% isolada através de um container Podman:

```bash
# 1. Compilar o binário contas-ci isoladamente pelo container Podman (sem precisar de Go no host):
./tools/ci/run_in_container.sh sh -c "cd tools/ci && go build -o ../../bin/contas-ci ./cmd/ci"

# 2. Executar a validação local completa (linter, formatação e testes com cobertura):
./bin/contas-ci check

# 3. Executar o ciclo completo de análise no SonarQube e validar o Quality Gate:
./bin/contas-ci sonar --sonar-url "http://192.168.1.20:9000"

# O script clássico ./sonar_check.sh permanece disponível (com fallback automático para Podman se Go não estiver instalado):
./sonar_check.sh
```
