# Feature 017: Camada de Autenticação com Login, Cadastro e Suporte a Google OAuth

## Contexto e Motivação
Atualmente o sistema funciona em modo mono-usuário/aberto, onde qualquer pessoa com acesso à rede local (porta 8501) pode visualizar e alterar contas, faturas e transações financeiras.
Para garantir privacidade e segurança em ambientes locais compartilhados ou em servidores acessíveis via rede externa, é indispensável estabelecer uma **camada de autenticação e controle de acesso** robusta, que ofereça:
1. **Cadastro e Login nativo**: criação de conta com Nome, E-mail, Login e Senha criptografada.
2. **Login social via Google OAuth 2.0**: autenticação simplificada e segura com contas Google corporativas ou pessoais.
3. **Isolamento de sessão e contexto de usuário**: proteção das páginas da aplicação Streamlit e dos endpoints de dados.

---

## Requisitos Funcionais

- **RF-001 (Modelo de Dados de Usuário)**:
  - Criar a tabela `user` via migração Alembic:
    - `id: UUID` (chave primária).
    - `name: str` (nome completo do usuário).
    - `email: str` (endereço de e-mail único, indexado).
    - `username: str` (login único, indexado).
    - `password_hash: str | None` (hash seguro de senha com bcrypt ou argon2, nulo se criado exclusivamente via Google OAuth).
    - `auth_provider: str` (`"local"` ou `"google"`).
    - `google_id: str | None` (ID do usuário no Google, se autenticado via OAuth).
    - `avatar_url: str | None` (foto de perfil opcional).
    - `is_active: bool` (padrão True).
    - `is_approved: bool` (padrão False para novos cadastros locais/Google; True para o primeiro usuário/admin do sistema).
    - `role: str` (`"admin"` para quem aprova, `"user"` para usuários comuns).
    - `created_at: datetime` e `updated_at: datetime`.

- **RF-002 (Cadastro e Login Local com Senha Segura)**:
  - Permitir novo cadastro na tela de login informando:
    - Nome completo.
    - E-mail válido.
    - Nome de usuário (login).
    - Senha (mínimo de 8 caracteres).
    - Confirmação de senha.
  - Validação de unicidade para `email` e `username`.
  - Criptografia irreversível da senha utilizando `bcrypt` / `passlib`.
  - Novos cadastros são criados com status `is_approved = False`.
  - Formulário de login aceitando username ou e-mail com senha:
    - Se credenciais estiverem corretas mas `is_approved = False`, impedir login e exibir aviso: "Conta aguardando aprovação do administrador."

- **RF-003 (Integração Google OAuth 2.0)**:
  - Suporte ao fluxo OpenID Connect / OAuth 2.0 do Google.
  - Variáveis de ambiente configuráveis em `.env`:
    - `GOOGLE_CLIENT_ID`
    - `GOOGLE_CLIENT_SECRET`
    - `GOOGLE_REDIRECT_URI`
  - Ao autenticar pelo Google:
    - Se o e-mail já existir e estiver aprovado, autenticar o usuário.
    - Se o usuário existir mas não estiver aprovado, exibir mensagem de aguardo de aprovação.
    - Se não existir, criar automaticamente o registro de usuário com `is_approved = False` e notificar que a conta precisa ser aprovada pelo administrador antes do primeiro acesso.

- **RF-004 (Controle de Sessão e Guard de Rotas no Streamlit)**:
  - Implementar interceptor/guard nas páginas do Streamlit:
    - Se o usuário não estiver autenticado (`st.session_state["authenticated"] is not True`), exibir exclusivamente a tela de Login / Cadastro.
    - Bloquear renderização de contas, faturas, transações e chat financeiro para sessões não autenticadas ou contas não aprovadas.
  - Header da aplicação com identificação do usuário logado (Nome, Foto ou avatar) e botão **"Sair" (Logout)** que invalida a sessão.

- **RF-005 (Isolamento Estrito Multi-Tenant por Usuário)**:
  - Cada usuário registrado possui seu próprio ecossistema financeiro isolado:
    - Adicionar coluna obrigatória `user_id: UUID` (com Foreign Key para `user.id` e índice) em todas as tabelas de dados:
      - `account` (`user_id`)
      - `category` (`user_id`)
      - `budget` (`user_id`)
      - `transaction` (`user_id`)
  - **Proibição de Compartilhamento / Vazamento entre Usuários**:
    - Nenhuma consulta (`SELECT`), listagem, filtro de extrato, cálculo de saldo, importação de fatura ou interação com o chat assistente de IA pode acessar ou modificar registros pertencentes a outro `user_id`.
    - Todas as queries nos repositórios e serviços devem injetar e filtrar obrigatoriamente pelo `user_id` da sessão ativa.
    - Se um usuário tentar acessar ou referenciar uma conta/transação de outro usuário, o sistema deve responder com erro de não encontrado ou acesso negado.
  - Ao criar uma nova conta de usuário aprovada, o sistema deve opcionalmente inicializar categorias padrão de receitas e despesas vinculadas exclusivamente ao seu `user_id`.

- **RF-006 (Aprovação de Contas de Usuários pelo Administrador)**:
  - **Status de Pendência**: Qualquer novo usuário cadastrado (seja via formulário local ou Google OAuth) nasce com `is_approved = False`.
  - **Painel Administrativo de Usuários**:
    - Usuário com role `"admin"` possui aba/seção exclusiva de "Gerenciamento de Usuários".
    - O administrador visualiza a lista de usuários pendentes de aprovação (com Nome, E-mail, Login, Data de Cadastro e Provedor) e usuários já aprovados/ativos.
    - O administrador pode clicar em **"Aprovar"** ou **"Rejeitar/Desativar"** cada usuário.
  - **Superusuário Inicial (Bootstrap)**:
    - O primeiro usuário cadastrado no sistema (ou definido via variável de ambiente `INITIAL_ADMIN_EMAIL`) recebe automaticamente `role = "admin"` e `is_approved = True`.

---

## Requisitos Não Funcionais

- **RNF-001 (Segurança de Credenciais)**: Senhas nunca devem ser salvas ou trafegadas em texto puro; utilizar salt e algoritmo `bcrypt` com fator de custo adequado.
- **RNF-002 (Configuração Segura de Cookies e Sessão)**: Chaves de sessão e segredos devem ser protegidos via `SECRET_KEY` configurável no `.env`.
- **RNF-003 (Extensibilidade e Conformidade)**: O fluxo de autenticação deve desacoplar a lógica de negócio dos frameworks web, seguindo a Clean Architecture (Use Cases: `RegisterUserUseCase`, `AuthenticateUserUseCase`, `GoogleOAuthCallbackUseCase`, `ApproveUserUseCase`).
- **RNF-004 (Garantia de Isolamento de Dados)**: Implementar testes automatizados de controle de acesso (multi-tenant) validando que o `Usuário B` não consegue visualizar contas, transações, orçamentos ou faturas criadas pelo `Usuário A`.
- **RNF-005 (Bloqueio de Contas Não Aprovadas)**: Garantir que usuários com `is_approved = False` recebam erro HTTP / bloqueio de sessão e não acessem nenhuma funcionalidade interna do sistema.
