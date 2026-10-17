# Feature 021: Gerenciamento de Identidade e Autenticação com Keycloak (OIDC / OAuth 2.0)

## Contexto e Motivação
Para centralizar e profissionalizar o gerenciamento de usuários, sessões, políticas de senha, provedores sociais (Identity Brokering) e controle de acesso baseado em papéis (RBAC), o projeto passa a contar com o **Keycloak** orquestrado no `docker-compose.yml` e integrado nativamente à aplicação via **OpenID Connect (OIDC) / OAuth 2.0**.

Esta especificação contempla:
1. **Infraestrutura Keycloak no Docker/Podman Compose**: Serviço `keycloak` integrado ao PostgreSQL, com importação automática do realm `contas`, client confidencial `contas-app` e roles `admin` e `user`.
2. **Configuração das Keys de Autenticação**: Variáveis de ambiente no `.env.example`, `docker-compose.yml` e `Settings` (`src/contas/config.py`) para conectar a aplicação ao Keycloak (URL pública, URL interna de rede de containers, Realm, Client ID, Client Secret e Redirect URI).
3. **Fluxo de Autenticação OIDC e Provisionamento Just-in-Time (JIT)**: Suporte a login via redirecionamento OIDC (Authorization Code Flow) e login direto (Direct Access Grants), sincronizando automaticamente o usuário do Keycloak com o banco local para preservar o isolamento multi-tenant (`user_id`).

---

## Requisitos Funcionais

- **RF-001 (Keycloak no `docker-compose.yml` com Realm Auto-Configurado)**:
  - Adicionar o serviço `keycloak` (`quay.io/keycloak/keycloak:26.0`) no `docker-compose.yml` conectado ao PostgreSQL (`db`) e à rede `contas_network`.
  - Criar configuração declarativa de Realm em `docker/keycloak/contas-realm.json` importada automaticamente na subida (`--import-realm`), contendo:
    - Realm: `contas` (registro de usuários e recuperação de senha habilitados).
    - Client OIDC: `contas-app` (confidencial, `standardFlowEnabled: true`, `directAccessGrantsEnabled: true`, `redirectUris: ["http://localhost:8501/*"]`).
    - Roles de Realm: `admin` e `user`.
  - Criar script de inicialização SQL em `docker/postgres/init-keycloak-db.sql` para garantir a existência do schema `keycloak` no PostgreSQL.

- **RF-002 (Configuração de Keys na Aplicação)**:
  - Adicionar em `src/contas/config.py`, `.env.example` e `docker-compose.yml`:
    - `KEYCLOAK_PORT`: porta pública exposta no host (padrão: `8180`, pois a porta `8080` já é utilizada por outro serviço no servidor `192.168.1.20`).
    - `KEYCLOAK_SERVER_URL`: URL pública do Keycloak acessível pelo navegador (ex: `http://localhost:8180` ou `http://192.168.1.20:8180`).
    - `KEYCLOAK_INTERNAL_URL`: URL interna para comunicação container-para-container entre `app` e `keycloak` (ex: `http://keycloak:8080`), com fallback automático para `KEYCLOAK_SERVER_URL`.
    - `KEYCLOAK_REALM`: nome do realm (padrão: `contas`).
    - `KEYCLOAK_CLIENT_ID`: identificador do client OIDC (padrão: `contas-app`).
    - `KEYCLOAK_CLIENT_SECRET`: chave secreta do client OIDC.
    - `KEYCLOAK_REDIRECT_URI`: URI de retorno após login (padrão: `http://localhost:8501`).

- **RF-003 (Serviço `KeycloakOAuthService` e Caso de Uso `KeycloakOAuthUseCase`)**:
  - Implementar `KeycloakOAuthService` em `src/contas/security/oauth_keycloak.py` com:
    - Geração de URL de autorização OIDC (`get_authorization_url`) e de registro (`get_registration_url`).
    - Troca de `authorization_code` por tokens e perfil OIDC (`exchange_code_for_user_info`), incluindo extração de roles do token JWT (`realm_access.roles` e `resource_access`).
    - Autenticação direta via credenciais (`authenticate_with_password`) usando Direct Access Grant do Keycloak.
  - Implementar `KeycloakOAuthUseCase` em `src/contas/application/use_cases/auth.py`:
    - Sincroniza o usuário autenticado no Keycloak com o repositório `IUserRepository` (`auth_provider = "keycloak"`).
    - Se o usuário possuir a role `admin` no Keycloak (ou for o primeiro usuário do sistema), atribui `role = "admin"` e `is_approved = True`.

- **RF-004 (Interface de Login Integrada ao Keycloak no Streamlit)**:
  - Atualizar `src/contas/ui/views/auth.py` para:
    - Interceptar o callback OIDC do Keycloak (`code` e `state=contas_keycloak`).
    - Exibir botões **"🔐 Entrar com Keycloak (SSO)"** e **"📝 Criar Conta no Keycloak"** quando configurado.
    - Permitir autenticação via Keycloak também pelo formulário de usuário/senha quando o Keycloak estiver ativo, mantendo fallback para autenticação local.

---

## Requisitos Não Funcionais

- **RNF-001 (Segurança e Zero Hardcoded Production Secrets)**: Chaves configuráveis via variáveis de ambiente (`.env`), sem expor segredos sensíveis em código-fonte.
- **RNF-002 (Clean Architecture & Isolamento Multi-Tenant)**: Manter `user_id` como chave de isolamento em todas as entidades de domínio.
- **RNF-003 (Qualidade SonarQube & Ruff Formatter)**: Cobertura de testes unitários para `KeycloakOAuthService` e `KeycloakOAuthUseCase`, aprovação no Ruff Formatter e no Quality Gate do SonarQube (`dc1`).
