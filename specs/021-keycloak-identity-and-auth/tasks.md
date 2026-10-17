# Tarefas de Implementação - Feature 021: Keycloak no Docker Compose e Autenticação OIDC

- [x] T001 [Docker] Criar configuração de Realm `docker/keycloak/contas-realm.json` e script `docker/postgres/init-keycloak-db.sql`
- [x] T002 [Compose] Adicionar serviço `keycloak` no `docker-compose.yml` (porta `8180`) e configurar variáveis de ambiente `KEYCLOAK_*` no serviço `app` e no `.env.example`
- [x] T003 [Config] Adicionar configurações do Keycloak (`keycloak_server_url`, `keycloak_internal_url`, `keycloak_realm`, `keycloak_client_id`, `keycloak_client_secret`, `keycloak_redirect_uri`) em `src/contas/config.py`
- [x] T004 [Security] Implementar `KeycloakOAuthService` e `KeycloakUserInfo` em `src/contas/security/oauth_keycloak.py`
- [x] T005 [UseCases] Adicionar `AuthProvider.KEYCLOAK`, schema `KeycloakAuthInput` e implementar `KeycloakOAuthUseCase` em `src/contas/application/use_cases/auth.py` e registrá-lo no `Container`
- [x] T006 [UI] Integrar callback OIDC, botões de login/cadastro Keycloak e fallback no formulário em `src/contas/ui/services.py` e `src/contas/ui/views/auth.py`
- [x] T007 [Tests & Quality] Criar testes unitários para `KeycloakOAuthService` e `KeycloakOAuthUseCase`, formatar com skill `formatter` e validar com `pytest`
