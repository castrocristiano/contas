import streamlit as st

from contas.config import settings
from contas.domain.errors import (
    AccountPendingApprovalError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from contas.security.oauth_google import GoogleOAuthService
from contas.ui.services import UIService


def _handle_google_callback() -> None:
    """Detects and processes Google OAuth 2.0 authorization code in query params."""
    code = st.query_params.get("code")
    if not code:
        return

    oauth_svc = GoogleOAuthService(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    )
    if not oauth_svc.is_configured:
        return

    try:
        user_info = oauth_svc.exchange_code_for_user_info(code)
        # Clear query params
        st.query_params.clear()

        user = UIService.google_oauth(
            google_id=user_info.google_id,
            email=user_info.email,
            name=user_info.name,
            avatar_url=user_info.avatar_url,
        )

        st.session_state["user"] = user
        st.session_state["authenticated"] = True
        st.success(f"Conectado com sucesso via Google, {user['name']}!")
        st.rerun()
    except AccountPendingApprovalError:
        st.query_params.clear()
        st.warning(
            "⏳ Sua conta Google foi registrada, mas ainda está **aguardando aprovação do administrador** para liberar o acesso."
        )
    except Exception as exc:  # noqa: BLE001
        st.query_params.clear()
        st.error(f"Erro ao autenticar com o Google: {exc}")


def render_auth_view() -> None:
    """Renders the Login and Registration screens in Streamlit."""
    _handle_google_callback()

    st.markdown(
        "<div style='text-align: center; margin-bottom: 2rem;'>"
        "<h1>🔐 Contas — Autenticação</h1>"
        "<p style='color: gray;'>Faça login para acessar suas contas, faturas e transações com isolamento seguro.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    oauth_svc = GoogleOAuthService(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    )
    google_configured = oauth_svc.is_configured
    google_auth_url = oauth_svc.get_authorization_url() if google_configured else "#"

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        tab_login, tab_register = st.tabs(["🔑 Entrar", "📝 Criar Cadastro"])

        with tab_login:
            st.subheader("Login no Sistema")

            # Google Login Button
            if google_configured:
                st.link_button(
                    "🌐 Entrar com o Google",
                    google_auth_url,
                    use_container_width=True,
                    type="secondary",
                )
                st.markdown(
                    "<div style='text-align: center; margin: 0.8rem 0; color: gray;'>ou</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption(
                    "ℹ️ Para ativar o login com o Google, defina `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` no arquivo `.env`."
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
                        user = UIService.authenticate_user(
                            identifier=login_ident.strip(),
                            password=login_pass,
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

            if google_configured:
                st.link_button(
                    "🌐 Cadastrar com o Google",
                    google_auth_url,
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
