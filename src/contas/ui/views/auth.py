import streamlit as st

from contas.config import settings
from contas.domain.errors import (
    AccountPendingApprovalError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from contas.security.oauth_keycloak import KeycloakOAuthService
from contas.ui.services import UIService


def _get_keycloak_service() -> KeycloakOAuthService:
    server_url = settings.keycloak_server_url
    redirect_uri = settings.keycloak_redirect_uri
    try:
        headers = st.context.headers
        host_header = headers.get("Host") or headers.get("host") or ""
        hostname = host_header.split(":")[0].strip()
        if hostname and hostname not in ("localhost", "127.0.0.1"):
            if "localhost" in server_url:
                server_url = server_url.replace("localhost", hostname)
            if "localhost" in redirect_uri:
                redirect_uri = redirect_uri.replace("localhost", hostname)
    except Exception:  # noqa: BLE001, S110
        pass

    return KeycloakOAuthService(
        server_url=server_url,
        internal_url=settings.keycloak_internal_url,
        realm=settings.keycloak_realm,
        client_id=settings.keycloak_client_id,
        client_secret=settings.keycloak_client_secret,
        redirect_uri=redirect_uri,
    )


def _handle_keycloak_callback(keycloak_svc: KeycloakOAuthService) -> None:
    """Detects and processes Keycloak OIDC authorization code in query params."""
    code = st.query_params.get("code")
    if not code or not keycloak_svc.is_configured:
        return
    try:
        user_info = keycloak_svc.exchange_code_for_user_info(code)
        st.query_params.clear()
        user = UIService.keycloak_oauth(
            keycloak_id=user_info.sub,
            email=user_info.email,
            username=user_info.username,
            name=user_info.name,
            roles=user_info.roles,
            avatar_url=user_info.avatar_url,
        )
        st.session_state["user"] = user
        st.session_state["authenticated"] = True
        st.success(f"Conectado com sucesso via Keycloak, {user['name']}!")
        st.rerun()
    except AccountPendingApprovalError:
        st.query_params.clear()
        st.warning(
            "⏳ Sua conta Keycloak foi registrada, mas ainda está **aguardando aprovação do administrador** para liberar o acesso."
        )
    except Exception as exc:  # noqa: BLE001
        st.query_params.clear()
        st.error(f"Erro ao autenticar com o Keycloak: {exc}")


def _authenticate_credentials(
    identifier: str, password: str, keycloak_svc: KeycloakOAuthService
) -> dict:
    """Authenticates via Keycloak Direct Grant first (if configured), falling back to local DB."""
    if keycloak_svc.is_configured:
        try:
            kc_info = keycloak_svc.authenticate_with_password(identifier, password)
            return UIService.keycloak_oauth(
                keycloak_id=kc_info.sub,
                email=kc_info.email,
                username=kc_info.username,
                name=kc_info.name,
                roles=kc_info.roles,
                avatar_url=kc_info.avatar_url,
            )
        except AccountPendingApprovalError:
            raise
        except Exception:  # noqa: BLE001, S110
            pass

    return UIService.authenticate_user(identifier=identifier, password=password)


def render_auth_view() -> None:
    """Renders the Login and Registration screens in Streamlit integrated with Keycloak."""
    keycloak_svc = _get_keycloak_service()
    _handle_keycloak_callback(keycloak_svc)

    st.markdown(
        "<div style='text-align: center; margin-bottom: 2rem;'>"
        "<h1>🔐 Contas — Autenticação</h1>"
        "<p style='color: gray;'>Faça login para acessar suas contas, faturas e transações com isolamento seguro.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    keycloak_configured = keycloak_svc.is_configured
    keycloak_auth_url = (
        keycloak_svc.get_authorization_url() if keycloak_configured else "#"
    )
    keycloak_reg_url = (
        keycloak_svc.get_registration_url() if keycloak_configured else "#"
    )

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        tab_login, tab_register = st.tabs(["🔑 Entrar", "📝 Criar Cadastro"])

        with tab_login:
            st.subheader("Login no Sistema")

            if keycloak_configured:
                st.link_button(
                    "🔐 Entrar com Keycloak (SSO)",
                    keycloak_auth_url,
                    use_container_width=True,
                    type="secondary",
                )
                st.markdown(
                    "<div style='text-align: center; margin: 0.8rem 0; color: gray;'>ou acesse diretamente abaixo</div>",
                    unsafe_allow_html=True,
                )

            with st.form("form_login"):
                login_ident = st.text_input(
                    "Usuário ou E-mail", placeholder="seu_usuario ou email@exemplo.com"
                )
                login_pass = st.text_input("Senha", type="password")
                btn_login = st.form_submit_button(
                    "Acessar", type="primary", use_container_width=True
                )

            if btn_login:
                if not login_ident.strip() or not login_pass:
                    st.error("Preencha usuário/e-mail e senha.")
                else:
                    try:
                        user = _authenticate_credentials(
                            identifier=login_ident.strip(),
                            password=login_pass,
                            keycloak_svc=keycloak_svc,
                        )
                        st.session_state["user"] = user
                        st.session_state["authenticated"] = True
                        st.success(f"Bem-vindo(a), {user['name']}!")
                        st.rerun()
                    except AccountPendingApprovalError:
                        st.warning(
                            "⏳ Sua conta foi criada, mas ainda está **aguardando aprovação do administrador** para acesso."
                        )
                    except InvalidCredentialsError:
                        st.error("Credenciais incorretas ou conta inativa.")
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Erro na autenticação: {exc}")

        with tab_register:
            st.subheader("Novo Cadastro")
            st.caption("Novas contas passam por aprovação prévia do administrador.")

            if keycloak_configured:
                st.link_button(
                    "🔐 Cadastrar via Keycloak",
                    keycloak_reg_url,
                    use_container_width=True,
                    type="secondary",
                )
                st.markdown(
                    "<div style='text-align: center; margin: 0.8rem 0; color: gray;'>ou preencha os dados abaixo:</div>",
                    unsafe_allow_html=True,
                )

            with st.form("form_register"):
                reg_name = st.text_input("Nome Completo", placeholder="ex: João Silva")
                reg_email = st.text_input("E-mail", placeholder="ex: joao@email.com")
                reg_username = st.text_input(
                    "Nome de Usuário (Login)", placeholder="ex: joaosilva"
                )
                reg_pass = st.text_input("Senha (mínimo 6 caracteres)", type="password")
                reg_pass2 = st.text_input("Confirme a Senha", type="password")
                btn_register = st.form_submit_button(
                    "Cadastrar", type="primary", use_container_width=True
                )

            if btn_register:
                if (
                    not reg_name.strip()
                    or not reg_email.strip()
                    or not reg_username.strip()
                ):
                    st.error("Por favor, preencha todos os campos obrigatórios.")
                elif reg_pass != reg_pass2:
                    st.error("As senhas informadas não coincidem.")
                elif len(reg_pass) < 6:
                    st.error("A senha deve ter no mínimo 6 caracteres.")
                else:
                    try:
                        created = UIService.register_user(
                            name=reg_name.strip(),
                            email=reg_email.strip(),
                            username=reg_username.strip(),
                            password=reg_pass,
                        )
                        if created.get("is_approved"):
                            st.success(
                                "✅ Conta de Administrador criada com sucesso! Faça login para começar."
                            )
                        else:
                            st.info(
                                "✅ Cadastro realizado com sucesso! Sua conta foi enviada para **aprovação do administrador**. Assim que aprovada, você poderá fazer login."
                            )
                    except UserAlreadyExistsError as exc:
                        st.error(str(exc))
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Erro ao cadastrar usuário: {exc}")
