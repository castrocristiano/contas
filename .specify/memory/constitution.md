<!--
Sync Impact Report
Version change: 1.1.0 -> 1.1.1
Modified principles:
  - Principle VI: Clarified that all source code, models, schemas, and tests MUST be written in English (EN-US), while documentation, specs, plans, and user interaction are in Brazilian Portuguese (PT-BR).
Added sections:
  - None
Removed sections:
  - None
Follow-up TODOs:
  - None
-->

# Contas Constitution

## Core Principles

### I. Simplicidade e YAGNI (Non-Negotiable)
Todo código, estrutura de dados e abstração arquitetural DEVEM atender a uma necessidade imediata e concreta do controle financeiro. É terminantemente proibido introduzir abstrações prematuras, camadas desnecessárias de indireção ou padrões de design complexos para cenários futuros hipotéticos. O sistema deve ser mantido enxuto, compreensível e fácil de manter.

### II. Integridade e Precisão Financeira
Valores monetários NUNCA devem ser representados por tipos de ponto flutuante binário (`float`). Todas as operações financeiras DEVEM utilizar representação decimal exata (`Decimal`) ou valores inteiros em centavos. Toda transação financeira DEVE conter data, descrição, valor, categoria, conta de origem/destino e status de liquidação com rastreabilidade explícita.

### III. Interface MCP Declarativa e Autônoma
A manipulação dos dados financeiros deve ser exposta primariamente através do Model Context Protocol (MCP). As ferramentas (tools) e recursos (resources) MCP DEVEM ser declarativos, com schemas estritos validados via Pydantic e mensagens de erro informativas. Isso assegura que agentes e modelos de linguagem possam consultar saldos, registrar gastos e gerar relatórios de forma determinística e segura.

### IV. Integração com IA Segura e Estruturada
Toda comunicação com a API da OpenAI (para categorização de despesas, extração de texto de comprovantes ou geração de insights) DEVE utilizar saídas estruturadas estritas (Structured Outputs / JSON Schema). A inteligência artificial não deve persistir dados diretamente no banco sem que passem pelas regras de validação de schema e integridade da aplicação.

### V. Conteinerização e Portabilidade com Podman
O sistema e seus serviços de suporte (servidor de aplicação/MCP e banco PostgreSQL) DEVEM ser completamente reproduzíveis e executáveis em containers utilizando `podman-compose` em modo rootless. Variáveis de ambiente e credenciais sensíveis (chaves da OpenAI, senhas de banco) NUNCA devem estar versionadas no código, devendo ser injetadas exclusivamente via arquivos de ambiente (`.env`).

### VI. Idioma: Documentação em PT-BR e Código-Fonte em EN-US
- **Documentação e Interação**: Todas as especificações de funcionalidades (`spec.md`), planos técnicos (`plan.md`), listas de tarefas (`tasks.md`), checklists, documentações e comunicação com o usuário DEVEM ser expressos em **Português do Brasil (PT-BR)**.
- **Código-Fonte em Inglês**: Todo o código-fonte executável (arquivos `.py`, classes, funções, variáveis, schemas Pydantic, tabelas e colunas no banco de dados, comentários de código e testes automatizados) DEVE ser escrito exclusivamente em **Inglês (EN-US)** (ex: `Account`, `Transaction`, `Category`, `amount`, `balance`, `transaction_type`).

## Stack Tecnológica e Restrições de Arquitetura

- **Linguagem e Runtime**: Python 3.12+ gerenciado pelo `uv`.
- **Servidor MCP e API**: Python MCP SDK oficial e Pydantic v2 para validação de dados.
- **Banco de Dados**: PostgreSQL 16+ gerenciado via `podman-compose`, com migrações de schema versionadas (Alembic / SQLModel / SQLAlchemy).
- **Provedor de LLM**: OpenAI API com integração direta usando `pydantic` para schemas de resposta.
- **Execução e Orquestração**: Podman e `podman-compose` com persistência de dados em volumes dedicados.

## Fluxo de Desenvolvimento e Qualidade

- **Gestão de Dependências**: Todas as adições ou alterações de bibliotecas DEVEM ser executadas exclusivamente via `uv add` ou `uv lock`.
- **Qualidade de Código e Formatação**: O código deve passar pelas regras de validação do `ruff` (linter e formatador).
- **Testes Automatizados**: Implementações de regras de cálculo, filtros de transações e ferramentas MCP DEVEM ser acompanhadas de testes automatizados com `pytest` e nomenclaturas em inglês.
- **Especificação Prévia**: Nenhuma funcionalidade significativa deve ser implementada sem especificação prévia via Spec Kit (`/speckit-specify` e `/speckit-plan`).

## Governance

A presente Constituição define a governança técnica e os princípios inegociáveis do projeto **Contas**. Todas as especificações, planos de implementação e revisões de código DEVEM obedecer rigorosamente a estas diretrizes.

- **Processo de Emenda**: Qualquer alteração, inclusão ou remoção de princípios requer justificativa explícita e atualização deste documento.
- **Versionamento Semântico da Constituição**:
  - **MAJOR**: Alterações ou remoções incompatíveis de princípios existentes.
  - **MINOR**: Inclusão de novos princípios ou diretrizes substanciais.
  - **PATCH**: Correções de texto, formatação e esclarecimentos semânticos.
- **Revisão de Conformidade**: Todas as tarefas executadas pelo Spec Kit devem validar conformidade com estes princípios antes da conclusão.

**Version**: 1.1.1 | **Ratified**: 2026-09-19 | **Last Amended**: 2026-09-19
