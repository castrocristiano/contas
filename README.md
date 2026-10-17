# Contas 💰 — Gestão Financeira Residencial Inteligente

[![CI & Tests](https://img.shields.io/github/actions/workflow/status/castrocristiano/contas/ci.yml?branch=main&label=CI%20%26%20Tests&logo=github)](https://github.com/castrocristiano/contas/actions)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Protocol%20Native-orange?logo=anthropic)](https://modelcontextprotocol.io/)
[![OpenAI Model](https://img.shields.io/badge/OpenAI-o3--mini%20(Default)-412991?logo=openai)](https://platform.openai.com/)
[![Identity Provider](https://img.shields.io/badge/Auth-Keycloak%2026%20(OIDC)-008AAA?logo=keycloak&logoColor=white)](https://www.keycloak.org/)
[![Framework](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%2016-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Container](https://img.shields.io/badge/Container-Podman%20%2F%20Docker-892CA0?logo=podman&logoColor=white)](https://podman.io/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> Sistema de gestão financeira pessoal e residencial construído sob os princípios de **Clean Architecture**, integrando assistentes de inteligência artificial através do padrão **Model Context Protocol (MCP)**, processamento inteligente de faturas em PDF via **OpenAI o3-mini**, gerenciamento centralizado de identidade com **Keycloak (OpenID Connect)**, isolamento estrito **multi-tenant** e esteira automatizada de CI/CD com **SonarQube Quality Gate**.

---

## 📑 Sumário

- [Visão Geral & Destaques](#-visão-geral--destaques)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Stack Tecnológica](#-stack-tecnológica)
- [Ferramentas MCP (Model Context Protocol)](#-ferramentas-mcp-model-context-protocol)
- [Como Executar](#-como-executar)
  - [Opção 1: Docker / Podman Compose (Recomendado)](#opção-1-docker--podman-compose-recomendado)
  - [Opção 2: Execução Local com uv](#opção-2-execução-local-com-uv)
- [Configuração de Ambiente (.env)](#-configuração-de-ambiente-env)
- [Gitflow & Esteira de CI/CD](#-gitflow--esteira-de-cicd)
- [Testes Automatizados & Qualidade (SonarQube)](#-testes-automatizados--qualidade-sonarqube)
- [Wiki do Projeto](#-wiki-do-projeto)
- [Licença](#-licença)

---

## 🌟 Visão Geral & Destaques

O **Contas** foi desenvolvido como um projeto demonstrativo de **engenharia de software moderna**, resolvendo dores reais de gestão financeira doméstica e integrando modelos de linguagem diretamente nos dados operacionais com segurança matemática e privacidade:

1. **Rigor e Precisão Financeira**: Uso exclusivo de `Decimal` em toda a cadeia (domínio, schemas e persistência), prevenindo erros de arredondamento de ponto flutuante binário (`float`).
2. **Clean Architecture Desacoplada**: A lógica de negócios independe da interface web (Streamlit) e do banco (PostgreSQL/SQLModel). Os casos de uso podem ser executados via MCP Server, CLI ou Frontend.
3. **Assistente de IA com MCP**: Qualquer cliente MCP (Claude Desktop, Antigravity, Cursor) pode consultar saldos, registrar despesas, liquidar lançamentos pendentes e checar limites orçamentários usando linguagem natural de forma padronizada.
4. **Parser Inteligente de Faturas PDF**: Extração com o modelo **OpenAI `o3-mini`**, com pré-filtragem local em Python, resiliência a layouts multi-coluna bancários e defesas estritas anti-alucinação.
5. **Autenticação Multi-Tenant com Keycloak (OIDC) e Aprovação**:
   - Gerenciamento de identidade centralizado com **Keycloak 26** (suportando SSO via navegador e login direto via *Direct Access Grant*, além de fallback local com `bcrypt`).
   - Cada usuário possui seus próprios dados 100% isolados por `user_id`.
   - Novos cadastros sem a role `admin` nascem pendentes de aprovação pelo Administrador (`role = 'admin'`).

---

## 🏛️ Arquitetura do Sistema

O projeto segue estritamente os preceitos da **Clean Architecture (Onion / Hexagonal)**:

```mermaid
flowchart TD
    subgraph UI_MCP["Camada de Entrada / Apresentação"]
        StreamlitApp["Streamlit Web UI<br>(Dashboard, Faturas, Chat)"]
        MCPServer["MCP Server<br>(14 Ferramentas Expostas)"]
    end

    subgraph Application["Camada de Aplicação (Use Cases & Ports)"]
        UseCases["Casos de Uso<br>(Accounts, Transactions, Budgets, Auth, Invoices)"]
        Ports["Portas de Repositório<br>(IAccountRepository, IUserRepository, ...)"]
        Container["Dependency Container<br>(Injeção de Dependências)"]
    end

    subgraph Domain["Camada de Domínio (Pure Python)"]
        Entities["Entidades de Domínio<br>(Account, Transaction, Budget, Category, User)"]
        Enums["Enums & Value Objects<br>(AccountType, TransactionType, AuthProvider, ...)"]
        Errors["Exceções de Domínio<br>(DomainError, UserNotFoundError, ...)"]
    end

    subgraph Infrastructure["Camada de Infraestrutura"]
        SQLAlchemyRepos["Repositórios SQLModel / SQLAlchemy<br>(Filtro estrito por user_id)"]
        Security["Módulos de Segurança<br>(Keycloak OIDC + bcrypt hash)"]
        PostgresDB[(PostgreSQL 16<br>Schemas: public & keycloak)]
        KeycloakIdP["Keycloak 26 IdP<br>(Realm: contas | Porta 8180)"]
        OpenAIClient["OpenAI Client<br>(o3-mini / Structured Outputs)"]
    end

    StreamlitApp --> Container
    MCPServer --> Container
    Container --> UseCases
    UseCases --> Ports
    UseCases --> Entities
    UseCases --> Errors
    SQLAlchemyRepos -.->|Implementa| Ports
    SQLAlchemyRepos --> PostgresDB
    UseCases --> Security
    Security --> KeycloakIdP
    KeycloakIdP --> PostgresDB
    StreamlitApp --> OpenAIClient
```

---

## 🚀 Funcionalidades Principais

| Módulo | Descrição |
| :--- | :--- |
| **🔐 Autenticação & Keycloak OIDC** | Login SSO e Direct Grant via Keycloak (realm `contas`), cadastro local com `bcrypt`, mapeamento de roles (`admin`/`user`) e painel administrativo de aprovação de usuários. |
| **🏢 Isolamento Multi-Tenant** | Todas as contas, categorias, transações e orçamentos são vinculados a um `user_id`. Nenhum dado é compartilhado entre usuários. |
| **📊 Dashboard & Extrato** | Visão patrimonial, saldo acumulado, gráfico de despesas por categoria, filtros dinâmicos por data de lançamento ou vencimento, liquidação de pendências e busca textual. |
| **💳 Compras Parceladas** | Registro de compras em parcelas com projeção automática em cascata, cálculo de valor total e consulta de plano de quitação. |
| **🧾 Importação de Fatura PDF** | Leitura automatizada de faturas de cartão de crédito bancárias (ex: Nubank, Itaú, Inter) com o modelo **OpenAI `o3-mini`**, seleção interativa de conta de destino e importação em lote. |
| **💬 Assistente de Chat com IA** | Chat financeiro integrado que entende perguntas em linguagem natural e utiliza ferramentas MCP para consultar e gerenciar suas finanças. |
| **🎯 Orçamentos & Metas** | Definição de limites mensais por categoria de despesa, com cálculo automático de porcentagem consumida e alertas visuais de estouro. |
| **⚙️ Configurações & Gestão em Lote** | Criação e renomeação de contas, gestão de categorias, exclusão segura (soft-delete ou cascade) e seleção múltipla. |

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Finalidade |
| :--- | :--- | :--- |
| **Linguagem & Runtime** | [Python 3.12+](https://www.python.org/) | Linguagem central de desenvolvimento |
| **Gerenciador de Pacotes** | [uv](https://github.com/astral-sh/uv) | Gerenciamento ultrarrápido de dependências e venvs |
| **Interface Web** | [Streamlit](https://streamlit.io/) | Dashboard reativo, visual e interativo |
| **Protocolo de IA** | [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) | Exposição declarativa de ferramentas para LLMs |
| **Modelos de IA** | [OpenAI `o3-mini`](https://platform.openai.com/) | Extração estruturada de PDFs e inteligência financeira |
| **Identidade & SSO** | [Keycloak 26](https://www.keycloak.org/) | Servidor OpenID Connect / OAuth 2.0 (porta `8180`) |
| **ORM & Validação** | [SQLModel](https://sqlmodel.tiangolo.com/) & [Pydantic v2](https://docs.pydantic.dev/) | Modelagem relacional tipada e validação rigorosa de schemas |
| **Banco de Dados** | [PostgreSQL 16](https://www.postgresql.org/) | Banco de dados transacional relacional com conformidade ACID |
| **Migrações** | [Alembic](https://alembic.sqlalchemy.org/) | Versionamento e evolução estruturada do esquema do banco |
| **Qualidade & Linter** | [SonarQube](https://www.sonarsource.com/products/sonarqube/) & [Ruff](https://docs.astral.sh/ruff/) | Quality Gate automatizado, cobertura de testes e regra estrita de Formatter |
| **Conteinerização** | [Podman](https://podman.io/) & [Docker](https://www.docker.com/) | Orquestração segura de múltiplos serviços via Compose |

---

## 🔌 Ferramentas MCP (Model Context Protocol)

O servidor MCP expõe **14 ferramentas tipadas** que permitem a qualquer IA interagir com as finanças:

```text
contas-server (MCP)
├── create_account           -> Cria nova conta com tipo e saldo inicial
├── list_accounts            -> Lista contas do usuário logado e patrimônio
├── update_account           -> Edita dados ou renomeia a conta
├── delete_account           -> Exclui ou desativa conta (com opção cascade)
├── record_transaction       -> Registra receita, despesa, transferência ou parcelamento
├── clear_transaction        -> Liquida transação pendente aplicando o impacto no saldo
├── get_statement            -> Extrato financeiro filtrado por período e tipo de data
├── get_installment_plan     -> Consulta status e parcelas de compras parceladas
├── delete_transaction       -> Exclui transações com reversão atômica de saldos
├── get_financial_summary    -> Resumo consolidado de receitas, despesas e saldo líquido
├── create_category          -> Cria categoria de receita ou despesa
├── list_categories          -> Lista categorias ativas do usuário
├── set_budget               -> Define teto orçamentário mensal para categoria
└── get_budget_status        -> Consulta consumo do orçamento no mês/ano
```

---

## 🚀 Como Executar

### Pré-requisitos
- **Git**
- **Docker & Docker Compose** (ou **Podman & Podman Compose**)
- Chave de API da OpenAI (caso deseje usar o assistente de IA e o importador de faturas)

---

### Opção 1: Docker / Podman Compose (Recomendado)

Sobe automaticamente o **PostgreSQL 16** (`5432`), o **Keycloak 26** (`8180`, importando automaticamente o realm `contas`) e a aplicação **Contas** (`8501`):

1. **Clone o repositório:**
   ```bash
   git clone git@github.com:castrocristiano/contas.git
   cd contas
   ```

2. **Crie o arquivo de configuração `.env`:**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env e insira sua OPENAI_API_KEY
   ```

3. **Inicie os serviços:**
   ```bash
   # Com Docker:
   docker compose up --build -d

   # Ou com Podman:
   podman-compose up --build -d
   ```

4. **Acesse no navegador:**
   - 🌐 **Aplicação Contas:** [http://localhost:8501](http://localhost:8501)
   - 🔐 **Console Admin do Keycloak:** [http://localhost:8180](http://localhost:8180) *(credenciais padrão em dev: `admin` / `admin`)*

---

### Opção 2: Execução Local com uv

1. **Instale o `uv` (caso não tenha):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Suba o banco PostgreSQL e o Keycloak via Compose:**
   ```bash
   docker compose up db keycloak -d  # ou: podman-compose up db keycloak -d
   ```

3. **Instale as dependências do projeto:**
   ```bash
   uv sync
   ```

4. **Aplique as migrações do banco com Alembic:**
   ```bash
   uv run alembic upgrade head
   ```

5. **Inicie a interface Web Streamlit:**
   ```bash
   uv run streamlit run src/contas/ui/app.py
   ```

---

## ⚙️ Configuração de Ambiente (.env)

Crie um arquivo `.env` na raiz do projeto (ou copie de `.env.example`):

```ini
# --- Banco de Dados PostgreSQL ---
POSTGRES_DB=contas
POSTGRES_USER=contas
POSTGRES_PASSWORD=contas
DATABASE_URL=postgresql+psycopg://contas:contas@localhost:5432/contas

# --- Inteligência Artificial (OpenAI) ---
OPENAI_API_KEY=sk-proj-sua-chave-aqui
INVOICE_MODEL=o3-mini

# --- Keycloak Identity Provider (OIDC) ---
KEYCLOAK_PORT=8180
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_SERVER_URL=http://localhost:8180
KEYCLOAK_INTERNAL_URL=http://keycloak:8080
KEYCLOAK_REALM=contas
KEYCLOAK_CLIENT_ID=contas-app
KEYCLOAK_CLIENT_SECRET=contas-keycloak-client-secret
KEYCLOAK_REDIRECT_URI=http://localhost:8501

# --- SonarQube ---
SONAR_TOKEN=seu-token-prioritario-do-sonarqube

# --- Aplicação ---
DEBUG=false
```

---

## 🔄 Gitflow & Esteira de CI/CD

O projeto adota um fluxo **Gitflow automatizado** integrado ao **GitHub Actions** (`.github/workflows/ci.yml`), onde cada push executa bateria de testes, validação de formatação (`ruff`), cobertura de código e **Quality Gate do SonarQube** antes de abrir Pull Requests ou gerar Releases:

```mermaid
flowchart LR
    subgraph DevFlow["Fluxo de Funcionalidades"]
        Feature["feature/* ou phase/*"] -->|Push + CI & Sonar OK| AutoPRDev["Auto-PR para develop"]
        AutoPRDev -->|Merge| Develop["develop"]
        Develop -->|CI & Sonar OK| AutoPRMain["Auto-PR para main"]
    end

    subgraph HotfixFlow["Fluxo de Correção Urgente (Hotfix)"]
        Hotfix["hotfix/* ou hotfix*"] -->|Push + CI & Sonar OK| AutoPRHotfix["Auto-PR direto para main"]
    end

    AutoPRMain -->|Merge| Main["main"]
    AutoPRHotfix -->|Merge| Main
    Main -->|CI & Sonar OK| Release["GitHub Release Automática<br>(v0.1.0-N ou bump MAJOR)"]
    Release -->|./update_remote.sh| ProdServer["Servidor Remoto (Podman Compose)"]
```

### Regras de Branches e Automação
1. **`feature/*` e `phase/*` (Novas Funcionalidades e Fases SDD)**:
   - Criadas a partir de `develop`.
   - Ao enviar `git push`, o CI roda **Build & Test** + **SonarQube Quality Gate**. Se aprovado, o job `auto-pr-to-develop` abre automaticamente um Pull Request para `develop`.
2. **`develop` (Branch de Integração)**:
   - Ao receber um merge e passar na esteira, o job `auto-pr-to-main` abre automaticamente um Pull Request de `develop` para `main`.
3. **`hotfix/*` e `hotfix*` (Correções Críticas em Produção)**:
   - Criadas a partir de `main` para correções urgentes.
   - Após aprovação nos testes e no SonarQube, o job `auto-pr-to-main` abre automaticamente o Pull Request **diretamente para a `main`** (`hotfix: <branch>`), sem precisar passar antes pela `develop`.
4. **`main` (Produção e Releases)**:
   - Todo merge na `main` (seja vindo de `develop` ou de `hotfix/*`) aciona o job `release-on-main`, que analisa os commits e gera automaticamente uma nova tag e **GitHub Release** (incrementando `MAJOR` automaticamente em caso de *breaking changes* ou gerando `v0.1.0-<run_number>`).
   - O servidor de produção (`192.168.1.20`) é atualizado com 1 comando via `./update_remote.sh`, que baixa a última Release publicada no GitHub, preserva o `.env` e reconstrói os containers.

---

## 🧪 Testes Automatizados & Qualidade (SonarQube)

O projeto possui validação rigorosa de código e testes automatizados:

```bash
# 1. Executar a Regra de Formatter (Ruff Check + Format + Relatórios Sonar)
python3 .agents/skills/formatter/scripts/sonar_formatter_check.py --fix

# 2. Executar toda a suíte de testes unitários e de integração (130+ testes)
uv run pytest

# 3. Executar análise completa no SonarQube (priorizando SONAR_TOKEN) e validar Quality Gate
./sonar_check.sh
```

---

## 📚 Wiki do Projeto

Para uma documentação aprofundada de arquitetura, fluxos e decisões de engenharia, consulte a [**Wiki Oficial no GitHub**](https://github.com/castrocristiano/contas/wiki):

- [Home](https://github.com/castrocristiano/contas/wiki)
- [01. Arquitetura & Clean Code](https://github.com/castrocristiano/contas/wiki/01-Arquitetura-e-Clean-Code)
- [02. Servidor MCP e Ferramentas](https://github.com/castrocristiano/contas/wiki/02-Servidor-MCP-e-Ferramentas)
- [03. Autenticação, Keycloak e Multi-Tenant](https://github.com/castrocristiano/contas/wiki/03-Autenticacao-e-Multi-Tenant)
- [04. Parser de Faturas e IA](https://github.com/castrocristiano/contas/wiki/04-Parser-de-Faturas-e-IA)
- [05. Guia de Instalação e Deploy](https://github.com/castrocristiano/contas/wiki/05-Guia-de-Instalacao-e-Deploy)
- [06. Metodologia Spec-Driven](https://github.com/castrocristiano/contas/wiki/06-Metodologia-Spec-Driven)
- [07. Gitflow, CI/CD e Qualidade (SonarQube)](https://github.com/castrocristiano/contas/wiki/07-Gitflow-e-CI-CD)

---

## 📄 Licença

Este projeto é distribuído sob a licença **GNU General Public License v3.0** (GPL-3.0). Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---
Desenvolvido por **[Cristiano Castro](https://github.com/castrocristiano)** como projeto de portfólio de engenharia de software e IA.
