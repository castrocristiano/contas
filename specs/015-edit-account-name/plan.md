# Plano de Implementação - Feature 015: Edição de Nome e Metadados da Conta

## 1. Camada de Domínio e Portas
- Em `src/contas/application/ports/repositories.py`:
  - Adicionar `update(account: Account) -> Account` na interface `IAccountRepository`.

## 2. Camada de Schemas
- Em `src/contas/schemas/account.py`:
  - Criar `UpdateAccountInput(BaseModel)` com campos `account_id: UUID`, `name: str | None = None` e `is_active: bool | None = None`.

## 3. Camada de Aplicação e Casos de Uso
- Em `src/contas/application/use_cases/accounts.py`:
  - Implementar `UpdateAccountUseCase`:
    - Buscar conta pelo `account_id`.
    - Lançar `AccountNotFoundError` se não existir.
    - Se `name` for fornecido, validar e atualizar.
    - Se `is_active` for fornecido, atualizar status.
    - Persistir via repositório e retornar entidade atualizada.

## 4. Infraestrutura e Repositório SQLAlchemy
- Em `src/contas/infrastructure/repositories/sqlmodel_account_repository.py`:
  - Implementar o método `update` persistindo as alterações no PostgreSQL via sessão assíncrona.

## 5. Servidor MCP e Camada de Apresentação
- Em `src/contas/server.py`:
  - Registrar tool `@mcp.tool() async def update_account(payload: UpdateAccountInput) -> dict`.
- Em `src/contas/ui/services.py`:
  - Adicionar `UIService.update_account(...)`.
- Em `src/contas/ui/app.py`:
  - Adicionar botão/popover de edição na listagem de contas com input de texto e confirmação.
- Em `src/contas/services/financial_chat.py`:
  - Adicionar `update_account` à lista de ferramentas de escrita com geração de resumo em `build_action_summary`.

## 6. Testes Automatizados
- `tests/unit/test_clean_architecture_use_cases.py`: teste unitário para `UpdateAccountUseCase`.
- `tests/integration/test_account_tools.py`: teste de integração para o handler `update_account`.
