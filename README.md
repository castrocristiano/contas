# Contas 💰 — Gestão Financeira Residencial Inteligente

[![CI & Tests](https://img.shields.io/github/actions/workflow/status/castrocristiano/contas/ci.yml?branch=main&label=CI%20%26%20Tests&logo=github)](https://github.com/castrocristiano/contas/actions)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Protocol%20Native-orange?logo=anthropic)](https://modelcontextprotocol.io/)
[![OpenAI Model](https://img.shields.io/badge/OpenAI-o3--mini%20(Default)-412991?logo=openai)](https://platform.openai.com/)
[![Framework](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%2016-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Container](https://img.shields.io/badge/Container-Podman%20%2F%20Docker-892CA0?logo=podman&logoColor=white)](https://podman.io/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> Sistema de gestão financeira pessoal e residencial construído sob os princípios de **Clean Architecture**, integrando assistentes de inteligência artificial através do padrão **Model Context Protocol (MCP)**, processamento inteligente de faturas em PDF via **OpenAI o3-mini**, autenticação com isolamento estrito **multi-tenant** e aprovação prévia por administrador.

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
- [Testes Automatizados & Qualidade](#-testes-automatizados--qualidade)
- [Wiki do Projeto](#-wiki-do-projeto)
- [Licença](#-licença)

---

## 🌟 Visão Geral & Destaques

O **Contas** foi desenvolvido como um projeto demonstrativo de **engenharia de software moderna**, resolvendo dores reais de gestão financeira doméstica e integrando modelos de linguagem diretamente nos dados operacionais com segurança matemática e privacidade:

1. **Rigor e Precisão Financeira**: Uso exclusivo de `Decimal` em toda a cadeia (domínio, schemas e persistência), prevenindo erros de arredondamento de ponto flutuante binário (`float`).
2. **Clean Architecture Desacoplada**: A lógica de negócios independe da interface web (Streamlit) e do banco (PostgreSQL/SQLModel). Os casos de uso podem ser executados via MCP Server, CLI ou Frontend.
3. **Assistente de IA com MCP**: Qualquer cliente MCP (Claude Desktop, Antigravity, Cursor) pode consultar saldos, registrar despesas e checar limites orçamentários usando linguagem natural de forma padronizada.
4. **Parser Inteligente de Faturas PDF**: Extração com o modelo **OpenAI `o3-mini`**, com pré-filtragem local em Python, resiliência a layouts multi-coluna bancários e defesas estritas anti-alucinação.
5. **Autenticação Multi-Tenant com Aprovação**:
   - Cada usuário possui seus próprios dados 100% isolados por `user_id`.
   - Novos cadastros nascem pendentes de aprovação pelo Administrador (`role = 'admin'`).
   - Suporte a login e cadastro com senha (`bcrypt`) e integração com **Google OAuth 2.0**.

---

## 🏛️ Arquitetura do Sistema

O projeto segue estritamente os preceitos da **Clean Architecture (Onion / Hexagonal)**:

```mermaid
flowchart TD
    subgraph UI_MCP["Camada de Entrada / Apresentação"]
        StreamlitApp["Streamlit Web UI<br>(Dashboard, Faturas, Chat)"]
        MCPServer["MCP Server<br>(13 Ferramentas Expostas)"]
    end

    subgraph Application["Camada de Aplicação (Use Cases & Ports)"]
        UseCases["Casos de Uso<br>(Accounts, Transactions, Budgets, Auth, Invoices)"]
        Ports["Portas de Repositório<br>(IAccountRepository, IUserRepository, ...)"]
        Container["Dependency Container<br>(Injeção de Dependências)"]
    end

    subgraph Domain["Camada de Domínio (Pure Python)"]
        Entities["Entidades de Domínio<br>(Account, Transaction, Budget, Category, User)"]
        Enums["Enums & Value Objects<br>(AccountType, TransactionType, ...)"]
        Errors["Exceções de Domínio<br>(DomainError, UserNotFoundError, ...)"]
    end

    subgraph Infrastructure["Camada de Infraestrutura"]
        SQLAlchemyRepos["Repositórios SQLModel / SQLAlchemy<br>(Filtro estrito por user_id)"]
        Security["Módulos de Segurança<br>(bcrypt hash, Google OAuth 2.0)"]
        PostgresDB[(PostgreSQL 16<br>Migrations com Alembic)]
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
    StreamlitApp --> OpenAIClient
```

---

## 🚀 Funcionalidades Principais

| Módulo | Descrição |
| :--- | :--- |
| **🔐 Autenticação & Acessos** | Cadastro local, Google OAuth, troca de senha e painel exclusivo para o Admin aprovar ou rejeitar novos cadastros. |
| **🏢 Isolamento Multi-Tenant** | Todas as contas, categorias, transações e orçamentos são vinculados a um `user_id`. Nenhum dado é compartilhado entre usuários. |
| **📊 Dashboard & Extrato** | Visão patrimonial, saldo acumulado, gráfico de despesas por categoria, filtros dinâmicos por data de lançamento ou vencimento e busca textual. |
| **💳 Compras Parceladas** | Registro de compras em parcelas com projeção automática em cascata, cálculo de valor total e consulta de plano de quitação. |
| **🧾 Importação de Fatura PDF** | Leitura automatizada de faturas de cartão de crédito bancárias (ex: Nubank, Itaú, Inter) com o modelo **OpenAI `o3-mini`**, seleção interativa e importação em lote. |
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
| **ORM & Validação** | [SQLModel](https://sqlmodel.tiangolo.com/) & [Pydantic v2](https://docs.pydantic.dev/) | Modelagem relacional tipada e validação rigorosa de schemas |
| **Banco de Dados** | [PostgreSQL 16](https://www.postgresql.org/) | Banco de dados transacional relacional com conformidade ACID |
| **Migrações** | [Alembic](https://alembic.sqlalchemy.org/) | Versionamento e evolução estruturada do esquema do banco |
| **Segurança** | [bcrypt](https://pypi.org/project/bcrypt/) & Google OAuth | Criptografia de senhas (rounds=12) e autenticação social |
| **Conteinerização** | [Podman](https://podman.io/) & [Docker](https://www.docker.com/) | Orquestração local segura com compose |

---

## 🔌 Ferramentas MCP (Model Context Protocol)

O servidor MCP expõe **13 ferramentas tipadas** que permitem a qualquer IA interagir com as finanças:

```text
contas-server (MCP)
├── create_account           -> Cria nova conta com tipo e saldo inicial
├── list_accounts            -> Lista contas do usuário logado e patrimônio
├── update_account           -> Edita dados ou renomeia a conta
├── delete_account           -> Exclui ou desativa conta (com opção cascade)
├── record_transaction       -> Registra receita, despesa, transferência ou parcelamento
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

4. **Acesse a aplicação no navegador:**
   - 🌐 **URL:** [http://localhost:8501](http://localhost:8501)

---

### Opção 2: Execução Local com uv

1. **Instale o `uv` (caso não tenha):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Suba o banco PostgreSQL via Compose:**
   ```bash
   docker compose up db -d  # ou: podman-compose up db -d
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

6. **(Opcional) Inicie o Servidor MCP:**
   ```bash
   uv run mcp dev src/contas/server.py   # Modo interativo (MCP Inspector)
   # ou
   uv run python -m contas             # Modo stdio nativo para Claude Desktop
   ```

---

## ⚙️ Configuração de Ambiente (.env)

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```ini
# --- Banco de Dados PostgreSQL ---
POSTGRES_DB=contas
POSTGRES_USER=contas
POSTGRES_PASSWORD=contas
DATABASE_URL=postgresql+psycopg://contas:contas@localhost:5432/contas

# --- Inteligência Artificial (OpenAI) ---
OPENAI_API_KEY=sk-proj-sua-chave-aqui
INVOICE_MODEL=o3-mini

# --- Google OAuth 2.0 (Opcional) ---
GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8501

# --- Aplicação ---
DEBUG=false
```

---

## 🧪 Testes Automatizados & Qualidade

O projeto conta com uma suíte abrangente de testes automatizados unitários e de integração, garantindo que regras financeiras e isolamento multi-tenant sejam respeitados:

```bash
# Executar toda a suíte de testes (124 testes)
uv run pytest

# Executar com relatório de cobertura de código
uv run pytest --cov=contas

# Executar verificação estática de tipos e formatação (Ruff)
uv run ruff check
uv run ruff format --check
```

---

## 📚 Wiki do Projeto

Para uma documentação aprofundada de arquitetura e decisões de engenharia, consulte a [**Wiki Oficial no GitHub**](https://github.com/castrocristiano/contas/wiki):

- [Home](https://github.com/castrocristiano/contas/wiki)
- [01. Arquitetura & Clean Code](https://github.com/castrocristiano/contas/wiki/01-Arquitetura-e-Clean-Code)
- [02. Servidor MCP e Ferramentas](https://github.com/castrocristiano/contas/wiki/02-Servidor-MCP-e-Ferramentas)
- [03. Autenticação e Multi-Tenant](https://github.com/castrocristiano/contas/wiki/03-Autenticacao-e-Multi-Tenant)
- [04. Parser de Faturas e IA](https://github.com/castrocristiano/contas/wiki/04-Parser-de-Faturas-e-IA)
- [05. Guia de Instalação e Deploy](https://github.com/castrocristiano/contas/wiki/05-Guia-de-Instalacao-e-Deploy)
- [06. Metodologia Spec-Driven](https://github.com/castrocristiano/contas/wiki/06-Metodologia-Spec-Driven)

---

## 📄 Licença

Este projeto é distribuído sob a licença **GNU General Public License v3.0** (GPL-3.0). Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---
Desenvolvido por **[Cristiano Castro](https://github.com/castrocristiano)** como projeto de portfólio de engenharia de software e IA.
