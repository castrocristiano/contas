# 🏛️ 01. Arquitetura & Clean Code

O projeto **Contas** foi desenhado e construído seguindo rigorosamente os princípios de **Clean Architecture** (Arquitetura Limpa / Hexagonal / Ports & Adapters), garantindo que as regras de negócio essenciais sejam completamente desacopladas de qualquer detalhe técnico, framework web, banco de dados ou protocolo de comunicação.

---

## 🎯 Princípios Fundamentais

1. **Independência de Frameworks**: A lógica financeira central não conhece Streamlit, MCP Server ou SQLAlchemy.
2. **Testabilidade Total**: Regras de negócio podem ser testadas com repositórios em memória (*In-Memory*) de forma instantânea sem precisar subir banco de dados.
3. **Independência de Banco de Dados**: A persistência relacional com PostgreSQL é apenas um detalhe da camada de infraestrutura.
4. **Precisão Matemática**: Proibição terminante do tipo `float` para qualquer cálculo monetário; uso exclusivo de `Decimal`.

---

## 🏗️ As Quatro Camadas do Sistema

### 1. Camada de Domínio (`src/contas/domain/`)
O núcleo do software, contendo entidades puras Python e regras invariantes:
- **Entidades**: `Account`, `Transaction`, `Budget`, `Category`, `User`.
- **Enums**: `AccountType`, `TransactionType`, `CategoryType`, `TransactionStatus`.
- **Exceções de Domínio**: `ContasError`, `AccountNotFoundError`, `InsufficientFundsError`, `InvalidCredentialsError`, `TransferSameAccountError`, etc.

### 2. Camada de Aplicação (`src/contas/application/`)
Orquestra os fluxos de trabalho e executa os casos de uso do sistema:
- **Use Cases**:
  - `CreateAccountUseCase`, `ListAccountsUseCase`, `UpdateAccountUseCase`, `DeleteAccountUseCase`, `BulkDeleteAccountsUseCase`.
  - `RecordTransactionUseCase`, `GetStatementUseCase`, `GetInstallmentPlanUseCase`, `DeleteTransactionUseCase`, `GetFinancialSummaryUseCase`.
  - `SetBudgetUseCase`, `GetBudgetStatusUseCase`.
  - `RegisterUserUseCase`, `AuthenticateUserUseCase`, `GoogleOAuthUseCase`, `ApproveUserUseCase`, `ChangePasswordUseCase`, `AdminResetPasswordUseCase`.
- **Portas (Interfaces de Repositório)**:
  - `IAccountRepository`, `ITransactionRepository`, `ICategoryRepository`, `IBudgetRepository`, `IUserRepository`.
- **Container de Injeção de Dependências**:
  - `Container` e `get_container()` provendo instâncias únicas configuradas com cache LRU.

### 3. Camada de Infraestrutura (`src/contas/infrastructure/`)
Implementações concretas que conectam o sistema com recursos externos:
- **Repositórios Relacionais**: `SQLAlchemyAccountRepository`, `SQLAlchemyTransactionRepository`, etc., utilizando SQLModel / PostgreSQL.
- **Segurança**: Criptografia de senhas com `bcrypt` e cliente Google OAuth.
- **Sessão & Banco**: Pool assíncrono via `AsyncEngine` e migrations com Alembic.

### 4. Camada de Apresentação / Entrada (`src/contas/ui/` e `src/contas/server.py`)
Mecanismos que recebem requisições dos usuários ou agentes:
- **Streamlit Web UI**: Interface visual e reativa.
- **MCP Server**: Servidor de protocolo com ferramentas tipadas expostas via stdio ou SSE.

---

## 🔒 Rigor com Precisão Monetária

Operações em ponto flutuante binário (`float`) possuem erros intrínsecos de representação (ex: `0.1 + 0.2 != 0.3`). Em aplicações financeiras, isso causa divergência de centavos e quebra de balancetes.

No **Contas**:
- Todos os saldos e valores são convertidos para `Decimal` imediatamente na borda da aplicação.
- No banco de dados, os campos são mapeados como `Numeric(18, 2)` ou centavos inteiros.
- Schemas Pydantic recebem valores como strings tipadas (ex: `"1500.50"`) para impedir conversões espúrias em JSON.
