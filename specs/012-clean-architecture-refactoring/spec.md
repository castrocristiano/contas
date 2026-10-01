# Feature Specification: Refatoração da Arquitetura para Clean Architecture (012-clean-architecture-refactoring)

**Feature Branch**: `feature/clean-architecture`

**Created**: 2026-09-30

**Status**: Draft 📝

**Input**: O projeto cresceu com novas funcionalidades (transações parceladas, faturas PDF, assistente de chat financeiro com function calling, projeções e orçamentos) e acumulou acoplamento direto entre camadas (ex.: ferramentas MCP e UI acessando o banco diretamente com SQLAlchemy e manipulando regras de negócio em handlers/views). Esta especificação define a refatoração para **Clean Architecture**, desacoplando domínio, regras de negócio/casos de uso, interfaces e infraestrutura externa.

---

## 1. Motivação e Objetivos

O codebase atual concentra regras de negócio vitais em arquivos de `tools/` e `ui/`:
1. **Regras de cálculo e negócio espalhadas**: Lógica de parcelamento, estorno de saldos em deleções, projeções futuras e categorizações estão divididas entre handlers MCP e a camada UI Streamlit.
2. **Acoplamento com SQLAlchemy e MCP**: Se quisermos trocar ou testar regras sem banco de dados real ou sem o framework MCP, encontramos forte acoplamento com sessões e modelos ORM.
3. **Complexidade crescente no Chat & Faturas**: Casos de uso de chat financeiro e parsing de faturas chamam serviços e repositórios sem contratos bem definidos de portas (ports) e adaptadores (adapters).

### Objetivos Principais:
- **Independência de Frameworks**: Domínio e casos de uso não dependem de FastMCP, Streamlit, SQLAlchemy ou OpenAI.
- **Testabilidade**: Casos de uso e entidades podem ser testados com mocks de repositórios em memória, sem necessidade de banco de dados ou chamadas externas.
- **Portas e Adaptadores (Hexagonal / Clean Architecture)**:
  - **Domínio**: Entidades ricas, Value Objects, Exceções de Domínio.
  - **Aplicação (Use Cases)**: Orquestração de casos de uso (ex.: `RecordTransactionUseCase`, `DeleteAccountUseCase`, `RefineInvoiceUseCase`). Interfaces de repositórios e serviços externos (Portas de saída).
  - **Interface / Adaptadores (Entrypoints)**: Controladores MCP (`tools`), Interface Web (`ui/app.py`), CLI.
  - **Infraestrutura**: Implementação de repositórios com SQLAlchemy, clientes externos (OpenAI, PDF reader).

---

## 2. Cenários de Usuário & Testes

### User Story 1 — Execução de Casos de Uso com Regras de Negócio Isoladas (Priority: P1)
Como desenvolvedor e mantenedor do sistema,  
Quero que as regras de negócio de transações, parcelamentos e saldos fiquem encapsuladas em Use Cases e Entidades de Domínio,  
Para que a lógica seja única, determinística e reutilizada igualmente pela UI Streamlit, Servidor MCP e Agente de Chat.

**Acceptance Scenarios**:
1. **Given** uma tentativa de registrar uma transação de transferência para a mesma conta, **When** o caso de uso `RecordTransactionUseCase` é acionado, **Then** uma exceção de domínio é levantada antes de qualquer chamada ao banco de dados.
2. **Given** a exclusão de uma conta com transações, **When** `DeleteAccountUseCase` é executado com ou sem flag `cascade`, **Then** a orquestração (desativação ou remoção com ajuste de saldos) é gerida puramente pela camada de aplicação.

---

### User Story 2 — Repositórios e Serviços Externos Desacoplados por Interfaces (Priority: P1)
Como engenheiro de software,  
Quero que a camada de aplicação dependa apenas de protocolos/interfaces (Ports),  
Para que possamos criar suites de testes rápidos sem I/O e trocar drivers de persistência com mínimo impacto.

**Acceptance Scenarios**:
1. **Given** a execução de testes unitários para `RecordTransactionUseCase`, **When** um repositório em memória (`InMemoryAccountRepository`) é injetado, **Then** o caso de uso executa com sucesso sem tocar no SQLite.
2. **Given** os adaptadores MCP e UI Streamlit, **When** requisitarem operações, **Then** ambos invocam os mesmos casos de uso através de injeção de dependência / container.

---

### User Story 3 — Camada de UI e MCP como Clientes de Casos de Uso (Priority: P2)
Como operador do sistema (via MCP ou Streamlit),  
Quero que ambas as interfaces funcionem de forma idêntica e sem duplicação de validações ou cálculos,  
Para manter a paridade funcional e evitar regressões existentes.

**Acceptance Scenarios**:
1. **Given** todas as ferramentas MCP (`contas/tools/*`), **When** invocadas por agentes de IA, **Then** elas apenas adaptam os inputs Pydantic, delegam para os Use Cases correspondentes e formatam o resultado estruturado.
2. **Given** a interface Streamlit (`contas/ui/*`), **When** o usuário efetua operações manuais, importa faturas ou conversa no chat, **Then** a interface utiliza os casos de uso da aplicação sem executar queries ORM diretas.

---

## 3. Requisitos Funcionais & Arquiteturais

- **RF-001**: O código DEVE ser reorganizado seguindo os 4 círculos da Clean Architecture:
  - `src/contas/domain/`: Entidades puras, Value Objects, Enums e Domain Errors.
  - `src/contas/application/`: Interfaces/Portas (`ports/repositories.py`, `ports/ai_service.py`), DTOs de entrada/saída e Casos de Uso (`use_cases/`).
  - `src/contas/infrastructure/`: Repositórios SQLAlchemy, banco de dados, cliente OpenAI e leitores de arquivos.
  - `src/contas/interfaces/`: Adaptadores primários/entradas: ferramentas MCP (`interfaces/mcp/`) e aplicação Streamlit (`interfaces/ui/`).
- **RF-002**: A camada de Domínio NÃO DEVE importar bibliotecas de infraestrutura (SQLAlchemy, Streamlit, FastMCP).
- **RF-003**: A camada de Aplicação DEVE depender apenas do Domínio e de abstrações (Protocol / ABC).
- **RF-004**: Todas as operações de escrita e leitura existentes DEVEM continuar suportadas sem quebra de contrato na API MCP nem na UI.
- **RF-005**: 100% dos testes unitários e de integração existentes DEVEM ser preservados e adaptados para garantir que não haja regressão funcional.

---

## 4. Critérios de Sucesso

- **CS-001**: Estrutura de pacotes segregada em `domain`, `application`, `infrastructure` e `interfaces`.
- **CS-002**: Zero importações de SQLAlchemy ou MCP dentro de `domain` e `application`.
- **CS-003**: Existência de repositórios em memória para testes unitários de casos de uso sem I/O.
- **CS-004**: Todas as 90+ validações de testes unitários e de integração passando com sucesso.
