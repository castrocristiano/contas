# Plano de Arquitetura e Implementação - Feature 018: Google OAuth e Troca de Senha

## 1. Visão Geral da Arquitetura
A Feature 018 aproveita a infraestrutura de dados já criada na Feature 017 (`user`, `auth_provider`, `google_id`, `password_hash`) e adiciona a camada interativa completa:
- Fluxo de OAuth 2.0 Web com troca de `code` por `token` e busca de dados do usuário (`userinfo`) no Google.
- Casos de uso e regras para troca de senha com verificação segura via `bcrypt`.
- Componentes visuais no Streamlit para o botão Google OAuth e formulário de perfil/troca de senha.

---

## 2. Camadas Envolvidas

### 2.1 Domain & Schemas
- Schemas em `src/contas/schemas/user.py`:
  - `ChangePasswordInput(user_id: UUID, current_password: str, new_password: str)`
  - `AdminResetPasswordInput(target_user_id: UUID, new_password: str)`
  - `GoogleOAuthCallbackInput(code: str, state: str | None = None)`
- Erros de Domínio em `src/contas/domain/errors.py`:
  - `InvalidCurrentPasswordError`
  - `PasswordMismatchError`

### 2.2 Security
- `src/contas/security/oauth_google.py`:
  - Implementar método assíncrono `exchange_code_for_user_info(code: str) -> GoogleUserInfo` usando `httpx` ou `requests`.
  - Método `get_authorization_url(state: str) -> str`.

### 2.3 Application (Use Cases)
- `src/contas/application/use_cases/auth.py`:
  - `ChangePasswordUseCase(user_repo)`:
    - Valida se o usuário existe.
    - Se o usuário tem `password_hash`, confere `verify_password(current_password, user.password_hash)`. Se incorreto, lança `InvalidCurrentPasswordError`.
    - Hasheia a nova senha com `hash_password(new_password)`.
    - Salva no repositório.
  - `AdminResetPasswordUseCase(user_repo)`:
    - Permite ao admin alterar a senha de qualquer usuário sem saber a senha antiga.
- Injetar use cases no `Container` (`src/contas/application/container.py`).

### 2.4 User Interface (Streamlit)
- `src/contas/ui/views/auth.py`:
  - Leitura de query params `st.query_params` na inicialização para detectar retorno do Google (`code` e `state`).
  - Se `code` for detectado: efetuar a troca de token e autenticar/registrar o usuário automaticamente, limpando os query params.
  - Botão estilizado **"Entrar com Google"** e **"Cadastrar com Google"** (link para a URL de autorização).
- `src/contas/ui/views/profile.py` ou seção na sidebar:
  - Adicionar aba ou seção **"🔒 Alterar Senha"**:
    - Campos de senha atual, nova senha e confirmação.
    - Tratamento amigável com mensagem de sucesso.
- `src/contas/ui/app.py`:
  - Integrar menu de perfil ou modal na barra lateral abaixo das informações do usuário.

---

## 3. Estratégia de Testes
- Testes unitários para `ChangePasswordUseCase`:
  - Troca com senha atual correta.
  - Rejeição quando a senha atual está incorreta.
  - Rejeição para senha com menos de 6 caracteres.
- Testes de integração do fluxo de usuários e `UIService`.
