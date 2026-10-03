# Feature 018: Cadastro e Login com Google OAuth 2.0 e Troca de Senha

## Contexto e Motivação
A Feature 017 implementou a infraestrutura base de usuários, campos no banco (`google_id`, `auth_provider`, `password_hash`), tabela de aprovação e isolamento multi-tenant por `user_id`.
No entanto, os botões e callbacks interativos de **Login e Cadastro via Google OAuth 2.0** no Streamlit e a funcionalidade de **Atualização / Redefinição de Senha** (pelo próprio usuário logado ou via solicitação) ainda precisam ser integrados e disponibilizados na interface visual.

Esta feature complementa o ecossistema de autenticação com:
1. **Login e Cadastro com Google OAuth 2.0**: Fluxo visual completo no Streamlit permitindo login e cadastro social com 1 clique.
2. **Atualização de Senha**: Funcionalidade para o usuário autenticado alterar sua senha atual informando senha anterior e nova senha com confirmação, além de permitir administradores redefinirem senhas se necessário.

---

## Requisitos Funcionais

- **RF-001 (Fluxo Visual do Google OAuth 2.0 no Streamlit)**:
  - Adicionar botão **"Entrar com o Google"** e **"Cadastrar com o Google"** estilizado na tela de autenticação.
  - Se as credenciais (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`) estiverem configuradas no `.env`:
    - Redirecionar o usuário para a tela de consentimento do Google (`accounts.google.com`).
    - Tratar o retorno (callback via `code` nos query params do Streamlit) capturando tokens e informações do perfil (nome, email, avatar, google_id).
    - Se o usuário já existir no banco:
      - Se `is_approved = True`, autentica imediatamente na sessão (`st.session_state["authenticated"] = True`).
      - Se `is_approved = False`, exibe aviso: *"Sua conta Google foi registrada, mas aguarda aprovação do administrador."*
    - Se o usuário não existir no banco:
      - Criar novo registro com `auth_provider = 'google'`, `is_approved = False` (ou `True` se for o primeiro usuário bootstrap).
      - Informar na tela que o cadastro foi criado e aguarda aprovação pelo administrador.
  - Se as credenciais do Google não estiverem presentes no `.env`, exibir aviso discreto informando que o login Google requer configuração de `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`.

- **RF-002 (Caso de Uso de Atualização de Senha)**:
  - Criar `ChangePasswordUseCase`:
    - Entrada: `user_id: UUID`, `current_password: str`, `new_password: str`.
    - Regras de validação:
      - Usuários autenticados exclusivamente via Google sem senha definida recebem instrução para definir sua primeira senha ou continuam usando Google.
      - Para contas locais com senha: a senha atual deve ser validada contra o hash armazenado com `verify_password`.
      - A nova senha deve ter no mínimo 6 caracteres e ser diferente da atual.
      - Atualizar o `password_hash` no repositório `IUserRepository` com novo salt `bcrypt`.
  - Criar `AdminResetPasswordUseCase`:
    - Permite ao administrador no painel de usuários redefinir a senha de um usuário local caso ele tenha esquecido.

- **RF-003 (Interface de Usuário para Troca de Senha)**:
  - Adicionar na barra lateral (sidebar) ou em um menu modal de **"Meu Perfil / Segurança"** um formulário para **Alterar Senha**:
    - Campo: Senha Atual
    - Campo: Nova Senha
    - Campo: Confirme a Nova Senha
    - Botão: "Salvar Nova Senha" com feedback de sucesso/erro.
  - No painel administrativo (`👥 Gerenciamento de Usuários`), permitir ao admin redefinir a senha provisória de um usuário cadastrado.

---

## Requisitos Não Funcionais

- **RNF-001 (Segurança de Hash)**: Utilizar `bcrypt` com salt seguro (rounds >= 12) para qualquer atualização de senha.
- **RNF-002 (Validação de Parâmetros)**: Esquemas validados via Pydantic (`ChangePasswordInput`, `AdminResetPasswordInput`).
- **RNF-003 (Clean Architecture)**: Lógica de negócio isolada em Use Cases independentes de framework web.
- **RNF-004 (Cobertura de Testes)**: Testes unitários para `ChangePasswordUseCase` e integração do fluxo.
