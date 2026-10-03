# Tarefas de Implementação - Feature 017: Autenticação, Cadastro e Isolamento Multi-Tenant

- [ ] T001 [Database] Criar migration Alembic para tabela `user` e adicionar FK `user_id` em `account`, `category`, `budget`, `transaction`
- [ ] T002 [Security] Implementar módulo de hashing de senhas e verificação com `bcrypt` em `src/contas/security/password.py`
- [ ] T003 [Security] Implementar fluxo de autenticação Google OAuth 2.0 em `src/contas/security/oauth_google.py`
- [ ] T004 [Domain] Criar entidade `User` e adicionar `user_id` às entidades existentes em `src/contas/domain/entities.py`
- [ ] T005 [UseCase] Implementar use cases `RegisterUserUseCase`, `AuthenticateUserUseCase` e `GoogleOAuthUseCase` em `src/contas/application/use_cases/auth.py`
- [ ] T006 [UseCase] Atualizar use cases existentes (`accounts`, `categories`, `budgets`, `transactions`) para exigir `user_id` obrigatório
- [ ] T007 [Repository] Implementar `SQLAlchemyUserRepository` e injetar filtro `.where(user_id == ...)` em todos os repositórios
- [ ] T008 [UI] Criar view de Login / Cadastro e botão de autenticação Google em `src/contas/ui/views/auth.py`
- [ ] T009 [UI] Adicionar interceptor de rota e gerenciamento de sessão de usuário em `src/contas/ui/app.py`
- [ ] T010 [UI] Atualizar `UIService` para propagar o `current_user_id` em todas as ações do usuário e faturas
- [ ] T011 [Tests] Criar testes unitários de autenticação e hash em `tests/unit/test_auth_use_cases.py`
- [ ] T012 [Tests] Criar testes de integração estritos de isolamento de dados entre usuários em `tests/integration/test_multi_tenant_isolation.py`
- [ ] T013 [Verification] Validar linters (`ruff check`), formatação (`ruff format`) e suíte de testes (`pytest`)
