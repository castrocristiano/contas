# Plano de Arquitetura e Implementação - Feature 021: Keycloak no Docker Compose e Autenticação OIDC

## 1. Visão Geral da Arquitetura
A integração com o **Keycloak** adiciona um provedor de identidade (IdP) padrão OpenID Connect (OIDC) à arquitetura do **Contas**:
- **Navegador do Usuário $\leftrightarrow$ Keycloak (`KEYCLOAK_SERVER_URL`, porta `8180`)**: Redirecionamento para tela de login/cadastro do Keycloak (a porta `8180` foi escolhida após inspeção no servidor `192.168.1.20`, onde a porta `8080` já estava ocupada).
- **Container da Aplicação (`contas-app`) $\leftrightarrow$ Container Keycloak (`KEYCLOAK_INTERNAL_URL`, `http://keycloak:8080`)**: Troca segura de `code` por `access_token` usando `KEYCLOAK_CLIENT_ID` e `KEYCLOAK_CLIENT_SECRET`, validação de `userinfo` e extração de roles.
- **Provisionamento Local (JIT)**: `KeycloakOAuthUseCase` vincula/cria o registro na tabela `user` do PostgreSQL, preservando o `user_id` em todas as operações financeiras.

---

## 2. Componentes da Solução

### 2.1 Infraestrutura (`docker-compose.yml` & `docker/`)
- `docker/postgres/init-keycloak-db.sql`: Cria o schema `keycloak` no banco PostgreSQL durante a inicialização.
- `docker/keycloak/contas-realm.json`: Define o realm `contas`, as roles `admin` e `user`, e o client confidencial `contas-app`.
- `docker-compose.yml`:
  - Adiciona serviço `keycloak` (`quay.io/keycloak/keycloak:26.0`) com `KC_DB=postgres`, `KC_DB_SCHEMA=keycloak`, `KC_HTTP_ENABLED=true`, `KC_HOSTNAME_STRICT=false`, porta `${KEYCLOAK_PORT:-8180}:8080` e volume `./docker/keycloak:/opt/keycloak/data/import:ro,Z`.
  - Injeta variáveis `KEYCLOAK_*` no serviço `app`.

### 2.2 Configuração (`src/contas/config.py` & `.env.example`)
- Campos adicionados em `Settings`:
  - `keycloak_server_url: str = "http://localhost:8180"`
  - `keycloak_internal_url: str = ""`
  - `keycloak_realm: str = "contas"`
  - `keycloak_client_id: str = "contas-app"`
  - `keycloak_client_secret: str = ""`
  - `keycloak_redirect_uri: str = "http://localhost:8501"`

### 2.3 Segurança & Domínio (`src/contas/security/oauth_keycloak.py`, `src/contas/models/user.py`, `src/contas/schemas/user.py`)
- `AuthProvider.KEYCLOAK = "keycloak"` em `src/contas/models/user.py`.
- `KeycloakAuthInput` em `src/contas/schemas/user.py`.
- `KeycloakOAuthService` em `src/contas/security/oauth_keycloak.py`:
  - Separa `public_base_url` (para links no navegador) e `internal_base_url` (para chamadas HTTP server-to-server `token` e `userinfo`).
  - Decodifica o payload JWT do `access_token` para extrair roles do realm (`realm_access.roles`) e do client (`resource_access`).

### 2.4 Aplicação & UI (`src/contas/application/use_cases/auth.py`, `src/contas/ui/services.py`, `src/contas/ui/views/auth.py`)
- `KeycloakOAuthUseCase`: cria ou atualiza o usuário local a partir dos dados vindos do Keycloak e valida status de aprovação.
- `UIService.keycloak_oauth`: ponte síncrona para o Streamlit.
- `render_auth_view` (`src/contas/ui/views/auth.py`):
  - Processa callback `?code=...&state=contas_keycloak`.
  - Renderiza botões de Login e Cadastro via Keycloak e integra autenticação de senha com Keycloak quando ativo.
