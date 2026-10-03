# Plano de Implementação - Feature 017: Autenticação, Cadastro e Isolamento Multi-Tenant

## 1. Modelos de Domínio e Migrações de Banco de Dados
- Em `migrations/`:
  - Criar migration Alembic para:
    1. Criar tabela `user` (`id`, `name`, `email`, `username`, `password_hash`, `auth_provider`, `google_id`, `avatar_url`, `is_active`, `created_at`, `updated_at`).
    2. Adicionar coluna `user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE` com índices nas tabelas:
       - `account`
       - `category`
       - `budget`
       - `transaction`

## 2. Camada de Domínio e Entidades
- Em `src/contas/domain/entities.py`:
  - Adicionar entidade `User`.
  - Adicionar atributo `user_id: UUID` nas entidades `Account`, `Category`, `Budget` e `Transaction`.

## 3. Segurança e Criptografia
- Em `src/contas/security/`:
  - `password.py`: funções `hash_password(raw_password: str) -> str` e `verify_password(raw_password: str, hashed: str) -> bool` via `bcrypt` / `pwdlib`.
  - `jwt.py` / `session.py`: criação e decodificação de tokens de sessão seguros.
  - `oauth_google.py`: cliente para troca de `code` por tokens do Google e recuperação de perfil do usuário.

## 4. Casos de Uso (Application Layer)
- Em `src/contas/application/use_cases/auth.py`:
  - `RegisterUserUseCase`: valida unicidade de e-mail e login, gera hash e cria usuário.
  - `AuthenticateUserUseCase`: valida credenciais locais (login/e-mail + senha).
  - `GoogleOAuthUseCase`: valida token do Google, cria usuário se novo ou vincula se existente.
- Atualizar casos de uso existentes (`accounts`, `categories`, `budgets`, `transactions`):
  - Todos passam a exigir `user_id: UUID` como contexto obrigatório de execução.

## 5. Repositórios e Isolamento de Queries (Infrastructure Layer)
- Em `src/contas/infrastructure/repositories/`:
  - `SQLAlchemyUserRepository`: busca por id, email, username ou google_id; criação e atualização.
  - Atualizar repositórios existentes (`Account`, `Category`, `Budget`, `Transaction`) para aplicar cláusula `.where(Model.user_id == user_id)` em **todas** as consultas de leitura e escrita.

## 6. Camada de Apresentação e UI (Streamlit)
- Em `src/contas/ui/`:
  - Criar tela de Login e Cadastro (`src/contas/ui/views/auth.py`):
    - Abas: "🔑 Entrar" e "📝 Criar Cadastro".
    - Botão "Continuar com o Google" (fluxo OAuth).
  - Interceptor no início do `app.py`:
    - Se `st.session_state.get("user")` não existir, renderizar exclusivamente a tela de autenticação.
    - Barra lateral com informações do usuário logado (nome, avatar) e botão "Sair".
  - Atualizar chamadas em `UIService` para injetar o `current_user_id` em todas as operações.

## 7. Testes Automatizados
- `tests/unit/test_auth_use_cases.py`: testes unitários de registro, login e validação de senhas.
- `tests/integration/test_multi_tenant_isolation.py`:
  - Criar `User A` e `User B`.
  - `User A` cria contas e transações.
  - Validar que `User B` listando contas ou extrato recebe lista vazia e não consegue acessar itens de `User A`.
