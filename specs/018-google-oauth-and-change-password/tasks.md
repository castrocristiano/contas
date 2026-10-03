# Tarefas de Implementação - Feature 018: Google OAuth e Troca de Senha

- [x] T001 [Security] Adicionar troca de token e obtenção de perfil Google (`exchange_code_for_user_info`) em `src/contas/security/oauth_google.py`
- [x] T002 [Schemas] Criar schemas `ChangePasswordInput` e `AdminResetPasswordInput` em `src/contas/schemas/user.py`
- [x] T003 [Domain] Adicionar erro de domínio `InvalidCurrentPasswordError` em `src/contas/domain/errors.py`
- [x] T004 [UseCase] Implementar `ChangePasswordUseCase` e `AdminResetPasswordUseCase` em `src/contas/application/use_cases/auth.py`
- [x] T005 [Container] Injetar novos use cases de troca de senha no container de injeção de dependência em `src/contas/application/container.py`
- [x] T006 [UIService] Adicionar métodos `change_password`, `admin_reset_password` e `handle_google_callback` em `src/contas/ui/services.py`
- [x] T007 [UI-Auth] Implementar botão "Continuar com o Google" e interceptor de callback OAuth via query params em `src/contas/ui/views/auth.py`
- [x] T008 [UI-Profile] Criar seção/modal de "Alterar Minha Senha" na interface do Streamlit em `src/contas/ui/app.py`
- [x] T009 [UI-Admin] Adicionar opção de redefinição de senha pelo Administrador na aba de Gerenciamento de Usuários
- [x] T010 [Tests] Criar testes unitários para troca de senha e redefinição em `tests/unit/test_change_password.py`
- [x] T011 [Verification] Validar linters (`ruff check`), formatação (`ruff format`) e suíte completa (`pytest`)
