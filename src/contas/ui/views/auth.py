import streamlit as st

from contas.domain.errors import (
    AccountPendingApprovalError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from contas.ui.services import UIService


def render_auth_view() -> None:
    """Renders the Login and Registration screens in Streamlit."""
    st.markdown(
        "<div style='text-align: center; margin-bottom: 2rem;'>"
        "<h1>🔐 Contas — Autenticação</h1>"
        "<p style='color: gray;'>Faça login para acessar suas contas, faturas e transações com isolamento seguro.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        tab_login, tab_register = st.tabs(["🔑 Entrar", "📝 Criar Cadastro"])

        with tab_login:
            st.subheader("Login no Sistema")
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
