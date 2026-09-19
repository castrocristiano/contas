# Contas 💰

Sistema inteligente de **gestão financeira doméstica** desenvolvido em Python, integrado ao ecossistema de Inteligência Artificial através do **Model Context Protocol (MCP)** e da API da **OpenAI**, executado de forma segura e conteinerizada com **Podman** (`podman-compose`) e persistência em **PostgreSQL**.

---

## 🎯 Visão Geral e Propósito

O **Contas** foi concebido para resolver o controle financeiro residencial de forma simples, automatizada e orientada a contexto:

- **Interface MCP Nativa**: Permite que assistentes inteligentes e LLMs (como Antigravity, Claude, VS Code AI) consultem saldos, busquem extratos e registrem receitas/despesas em linguagem natural de forma padronizada.
- **Integridade e Precisão Financeira**: Rigor absoluto nos cálculos matemáticos através do uso exclusivo de tipos decimais exatos (`Decimal`/centavos), eliminando erros de arredondamento inerentes a ponto flutuante binário (`float`).
- **Automação com IA**: Categorização automática de comprovantes e transações financeiras com a API da OpenAI utilizando saídas estruturadas estritas (*Structured Outputs*).
- **Simplicidade e YAGNI**: Foco direto em resolver necessidades reais sem sobrecarga de abstrações prematuras ou complexidade desnecessária.

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Papel no Projeto |
| :--- | :--- | :--- |
| **Linguagem & Runtime** | [Python 3.12+](https://www.python.org/) | Linguagem base de implementação |
| **Gerenciador de Pacotes** | [uv](https://github.com/astral-sh/uv) | Gerenciamento ultrarrápido de dependências e ambientes virtuais |
| **Protocolo de IA** | [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) | Exposição declarativa de ferramentas (*Tools*) e recursos (*Resources*) |
| **Validação de Dados** | [Pydantic v2](https://docs.pydantic.dev/) | Schemas estritos para validação de entradas de ferramentas e modelos de dados |
| **Banco de Dados** | [PostgreSQL 16+](https://www.postgresql.org/) | Persistência relacional com conformidade ACID e integridade referencial |
| **Provedor de LLM** | [OpenAI API](https://platform.openai.com/) | Extração estruturada de dados, categorização e insights financeiros |
| **Conteinerização** | [Podman](https://podman.io/) & `podman-compose` | Orquestração local segura, reprodutível e rootless |
| **Metodologia** | [GitHub Spec Kit](https://github.com/github/spec-kit) | Desenvolvimento orientado a especificações (*Spec-Driven Development*) |

---

## 🏛️ Governança e Regras do Projeto

O projeto é regido pelos princípios formais estabelecidos na [**Constituição do Projeto**](.specify/memory/constitution.md) e pelas diretrizes de [**AGENTS.md**](AGENTS.md):

1. **Simplicidade e YAGNI (Non-Negotiable)**: Nenhuma abstração sem uso imediato comprovado.
2. **Integridade Financeira**: Proibição estrita de `float` para valores monetários.
3. **Interface MCP Declarativa**: Operações expostas como ferramentas tipadas com validação Pydantic.
4. **IA Segura**: Validação de schema pré-persistência em qualquer resposta vinda da OpenAI.
5. **Isolamento com Podman**: Toda a infraestrutura sobe via `podman-compose` em modo rootless.
6. **Convenção de Idiomas**:
   - **Documentação e Interação**: **Português do Brasil (PT-BR)** para especificações (`spec.md`), planos (`plan.md`), tarefas (`tasks.md`), checklists, documentação e comunicação com o usuário.
   - **Código-Fonte**: **Inglês (EN-US)** estrito para classes, funções, variáveis, schemas Pydantic, tabelas/colunas SQL e testes (ex: `Account`, `Transaction`, `Category`, `create_account`, `amount`, `balance`).

---

## 📂 Estrutura do Repositório

```text
contas/
├── .agents/                    # Configurações, regras e skills para o Antigravity
│   ├── rules/                  # Regras ativas (ex: idioma.md)
│   └── skills/                 # Skills do Spec Kit (speckit-specify, speckit-plan, etc.)
├── .specify/                   # Infraestrutura e templates do Spec Kit
│   ├── memory/
│   │   └── constitution.md     # Constituição e princípios fundamentais do projeto
│   └── templates/              # Templates de especificações, planos e tarefas
├── specs/                      # Especificações de funcionalidades versionadas
│   └── 001-core-infra-mcp/     # Feature: Infraestrutura Base e Servidor MCP
│       ├── spec.md             # Especificação funcional detalhada
│       └── checklists/         # Checklists de qualidade de requisitos
├── AGENTS.md                   # Diretrizes para assistentes e agentes de IA
├── LICENSE                     # Licença GNU General Public License v3.0
└── README.md                   # Este documento
```

---

## 🚀 Como Desenvolver

### Pré-requisitos

- **Python 3.12+**
- **uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Podman & Podman Compose**: Para rodar os serviços locais

### Fluxo de Trabalho com Spec Kit

O desenvolvimento de novas funcionalidades segue o ciclo do **Spec-Driven Development**:

1. **Especificar**:
   ```text
   /speckit-specify Descreva a funcionalidade que deseja criar...
   ```
2. **Planejar**:
   ```text
   /speckit-plan
   ```
3. **Gerar Tarefas**:
   ```text
   /speckit-tasks
   ```
4. **Implementar**:
   ```text
   /speckit-implement
   ```

---

## 🚀 Como Executar

### 1. Inicializar infraestrutura e banco de dados

```bash
# Subir o banco PostgreSQL via podman-compose
podman-compose up -d

# Executar as migrações do banco com Alembic
uv run alembic upgrade head
```

### 2. Iniciar o Servidor MCP

```bash
# Modo inspeção interativa via browser (MCP Inspector)
uv run mcp dev src/contas/server.py

# Ou execução direta via módulo stdio (para Claude Desktop / Antigravity)
uv run python -m contas
```

---

## 🛠️ Ferramentas MCP Disponíveis

O servidor expõe as seguintes ferramentas em conformidade com o protocolo MCP:

- `create_account`: Cria uma nova conta financeira com saldo inicial.
- `list_accounts`: Lista todas as contas com saldo atual e soma consolidada.
- `record_transaction`: Registra receita, despesa ou transferência atualizando saldos atomicamente.
- `get_statement`: Retorna o extrato detalhado de uma conta em determinado período com resumo.
- `get_financial_summary`: Consolida patrimônio total de todas as contas ativas.
- `health_check`: Verifica o status operacional do servidor MCP e conexão com PostgreSQL.

Para detalhes de schemas de entrada e saída, consulte o documento de [Contratos MCP](specs/001-core-infra-mcp/contracts/mcp-tools.md).

---

## 📄 Licença

Este projeto é distribuído sob a licença **GNU General Public License v3.0** (GPL-3.0). Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

