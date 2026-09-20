from datetime import UTC, datetime, timedelta
from uuid import UUID

import pandas as pd
import streamlit as st

from contas.models.account import AccountType
from contas.models.category import CategoryType
from contas.models.transaction import TransactionType
from contas.services.financial_chat import (
    PendingAction,
    chat_with_financial_assistant,
    execute_pending_action,
)
from contas.ui.services import UIService

# Configuração da Página
st.set_page_config(
    page_title="Contas — Gestão Financeira",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


def format_currency(value_str: str | float) -> str:
    val = float(value_str)
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def run_app():
    import sys

    from streamlit.web import cli as stcli

    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())


def main():
    st.sidebar.title("💰 Contas")
    st.sidebar.caption("Gestão Financeira Residencial Inteligente")

    menu = st.sidebar.radio(
        "Navegação",
        [
            "📊 Dashboard & Extrato",
            "➕ Novo Lançamento",
            "🧾 Importar Fatura PDF",
            "💬 Assistente Financeiro",
            "🎯 Orçamentos & Metas",
            "⚙️ Configurações",
        ],
        index=0,
    )

    # -------------------------------------------------------------
    # 1. DASHBOARD & EXTRATO
    # -------------------------------------------------------------
    if menu == "📊 Dashboard & Extrato":
        st.title("📊 Visão Geral das Finanças")

        # Carregar Contas
        accounts_data = UIService.list_accounts()
        accounts = accounts_data.get("accounts", [])
        total_balance = sum(float(a["balance"]) for a in accounts)

        # Métricas no Topo
        col_total, col_acc_count = st.columns([2, 1])
        with col_total:
            st.metric("Patrimônio Total", format_currency(total_balance))
        with col_acc_count:
            st.metric("Contas Ativas", len(accounts))

        st.subheader("💳 Saldos por Conta")
        if accounts:
            cols = st.columns(min(len(accounts), 4))
            for i, acc in enumerate(accounts):
                with cols[i % 4]:
                    st.container(border=True).metric(
                        label=f"{acc['name']} ({acc['account_type'].upper()})",
                        value=format_currency(acc["balance"]),
                    )
        else:
            st.info(
                "Nenhuma conta cadastrada. Cadastre uma conta no menu 'Novo Lançamento' ou 'Configurações'."
            )

        st.divider()

        # Seção de Extrato
        st.subheader("📜 Extrato de Movimentações")
        if accounts:
            filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(
                [2, 1, 1, 1]
            )
            with filter_col1:
                selected_acc_name = st.selectbox(
                    "Conta",
                    options=[a["name"] for a in accounts],
                    index=0,
                )
                selected_acc = next(
                    a for a in accounts if a["name"] == selected_acc_name
                )

            with filter_col2:
                today = datetime.now(UTC).date()
                start_date = st.date_input(
                    "Data Inicial", value=today - timedelta(days=30)
                )
            with filter_col3:
                end_date = st.date_input("Data Final", value=today + timedelta(days=60))
            with filter_col4:
                include_pending = st.checkbox(
                    "Incluir parcelas futuras/pendentes", value=True
                )

            if selected_acc:
                statement = UIService.get_statement(
                    account_id=UUID(selected_acc["id"]),
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    include_pending=include_pending,
                )

                txs = statement.get("transactions", [])
                if txs:
                    summary = statement.get("summary", {})
                    sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
                    sum_col1.metric(
                        "Receitas", format_currency(summary.get("total_income", "0.00"))
                    )
                    sum_col2.metric(
                        "Despesas",
                        format_currency(summary.get("total_expense", "0.00")),
                    )
                    sum_col3.metric(
                        "Resultado Líquido", format_currency(summary.get("net", "0.00"))
                    )
                    sum_col4.metric("Qtd. Transações", summary.get("count", 0))

                    # Tabela formatada
                    df_data = []
                    for t in txs:
                        inst_info = ""
                        if t.get("installment_number") and t.get("total_installments"):
                            inst_info = (
                                f"{t['installment_number']}/{t['total_installments']}"
                            )

                        df_data.append(
                            {
                                "Data": datetime.fromisoformat(
                                    t["transaction_date"]
                                ).strftime("%d/%m/%Y"),
                                "Descrição": t["description"],
                                "Categoria": t.get("category") or "—",
                                "Tipo": t["transaction_type"].upper(),
                                "Status": "Liquidado"
                                if t["status"] == "cleared"
                                else "Pendente",
                                "Parcela": inst_info or "À vista",
                                "Valor": format_currency(t["amount"]),
                            }
                        )
                    st.dataframe(
                        pd.DataFrame(df_data), width="stretch", hide_index=True
                    )

                    # Ações de Gerenciamento / Exclusão
                    with st.expander("🗑️ Excluir Lançamento"):
                        st.caption(
                            "Selecione uma transação para excluir. Se a transação for liquidada, o saldo será estornado automaticamente."
                        )
                        tx_options = {
                            f"{datetime.fromisoformat(t['transaction_date']).strftime('%d/%m/%Y')} - {t['description']} ({format_currency(t['amount'])}) [{t['id'][:8]}]": t
                            for t in txs
                        }
                        selected_label = st.selectbox(
                            "Escolha a transação",
                            options=list(tx_options.keys()),
                            key="select_tx_delete",
                        )

                        if selected_label:
                            chosen_tx = tx_options[selected_label]
                            is_inst = bool(chosen_tx.get("installment_id"))

                            delete_all = False
                            if is_inst:
                                st.info(
                                    f"Esta transação faz parte de uma compra parcelada ({chosen_tx.get('installment_number')}/{chosen_tx.get('total_installments')})."
                                )
                                delete_all = st.checkbox(
                                    "Excluir TODAS as parcelas desta compra parcelada",
                                    value=False,
                                    help="Se marcado, remove todas as parcelas do plano e estorna as que já foram liquidadas.",
                                )

                            col_del_btn, _ = st.columns([1, 4])
                            with col_del_btn:
                                if st.button(
                                    "Confirmar Exclusão",
                                    type="primary",
                                    key="btn_confirm_delete_tx",
                                ):
                                    del_res = UIService.delete_transaction(
                                        transaction_id=UUID(chosen_tx["id"]),
                                        delete_all_installments=delete_all,
                                    )
                                    if "error" in del_res:
                                        st.error(
                                            f"Erro ao excluir: {del_res['error']['message']}"
                                        )
                                    else:
                                        st.success(
                                            del_res.get(
                                                "message",
                                                "Transação excluída com sucesso!",
                                            )
                                        )
                                        st.rerun()
                else:
                    st.info("Nenhuma transação encontrada no período selecionado.")

    # -------------------------------------------------------------
    # 2. NOVO LANÇAMENTO
    # -------------------------------------------------------------
    elif menu == "➕ Novo Lançamento":
        st.title("➕ Registrar Transação")

        accounts_data = UIService.list_accounts()
        accounts = accounts_data.get("accounts", [])

        if not accounts:
            st.warning("Cadastre uma conta antes de realizar lançamentos.")
        else:
            categories_data = UIService.list_categories()
            categories = categories_data.get("categories", [])

            with st.form("form_transaction"):
                tipo = st.selectbox(
                    "Tipo de Transação", ["Despesa", "Receita", "Transferência"]
                )

                col1, col2 = st.columns(2)
                with col1:
                    valor = st.text_input("Valor (R$)", placeholder="ex: 150.00")
                    descricao = st.text_input(
                        "Descrição", placeholder="ex: Almoço de domingo"
                    )

                with col2:
                    data_tx = st.date_input(
                        "Data do Lançamento", value=datetime.now(UTC).date()
                    )
                    conta_origem = st.selectbox(
                        "Conta de Origem",
                        options=[a["name"] for a in accounts],
                    )

                conta_dest = None
                if tipo == "Transferência":
                    conta_dest = st.selectbox(
                        "Conta de Destino",
                        options=[
                            a["name"] for a in accounts if a["name"] != conta_origem
                        ],
                    )

                categoria = None
                if tipo != "Transferência" and categories:
                    filtered_cats = [
                        c
                        for c in categories
                        if (tipo == "Despesa" and c["category_type"] == "expense")
                        or (tipo == "Receita" and c["category_type"] == "income")
                    ]
                    categoria = st.selectbox(
                        "Categoria",
                        options=[c["name"] for c in filtered_cats],
                    )

                # Opção de Parcelamento (apenas para despesa)
                is_parcelada = False
                qtd_parcelas = 1
                if tipo == "Despesa":
                    st.subheader("💳 Opção de Parcelamento")
                    is_parcelada = st.checkbox("Esta despesa é parcelada?")
                    if is_parcelada:
                        qtd_parcelas = st.number_input(
                            "Número de Parcelas",
                            min_value=2,
                            max_value=72,
                            value=3,
                            step=1,
                        )
                        st.caption(
                            "A primeira parcela será debitada na data selecionada; as parcelas restantes serão agendadas mensalmente com status pendente."
                        )

                submitted = st.form_submit_button(
                    "Confirmar Lançamento", type="primary"
                )
                if submitted:
                    try:
                        acc_source = next(
                            a for a in accounts if a["name"] == conta_origem
                        )
                        acc_dest = next(
                            (a for a in accounts if a["name"] == conta_dest), None
                        )
                        cat_obj = next(
                            (c for c in categories if c["name"] == categoria), None
                        )

                        tipo_map = {
                            "Despesa": TransactionType.EXPENSE,
                            "Receita": TransactionType.INCOME,
                            "Transferência": TransactionType.TRANSFER,
                        }

                        res = UIService.record_transaction(
                            amount=valor,
                            transaction_type=tipo_map[tipo],
                            source_account_id=UUID(acc_source["id"]),
                            destination_account_id=UUID(acc_dest["id"])
                            if acc_dest
                            else None,
                            category_id=UUID(cat_obj["id"]) if cat_obj else None,
                            description=descricao,
                            transaction_date=f"{data_tx.isoformat()}T12:00:00Z",
                            total_installments=qtd_parcelas if is_parcelada else None,
                            total_amount=valor if is_parcelada else None,
                        )

                        if "error" in res:
                            st.error(f"Erro ao registrar: {res['error']['message']}")
                        else:
                            st.success("Transação registrada com sucesso!")
                            st.rerun()
                    except (ValueError, KeyError, TypeError) as exc:
                        st.error(f"Erro de validação: {exc}")

    # -------------------------------------------------------------
    # 3. IMPORTAR FATURA PDF & CHAT INTERATIVO
    # -------------------------------------------------------------
    elif menu == "🧾 Importar Fatura PDF":
        from contas.services.invoice_parser import (
            check_pdf_encrypted,
            extract_text_from_pdf,
            parse_invoice_with_openai,
            refine_items_with_chat,
        )

        st.title("🧾 Importar Fatura de Cartão (PDF)")
        st.caption(
            "Carregue sua fatura em PDF, use o chat interativo para filtrar despesas com IA e importe os lançamentos com um clique."
        )

        accounts_data = UIService.list_accounts()
        accounts = accounts_data.get("accounts", [])
        categories_data = UIService.list_categories(category_type="expense")
        categories = categories_data.get("categories", [])
        category_names = [c["name"] for c in categories]

        if not accounts:
            st.warning("Cadastre uma conta antes de importar faturas.")
            st.stop()

        col_cfg1, col_cfg2 = st.columns([1, 1])
        with col_cfg1:
            selected_acc_name = st.selectbox(
                "Conta de Destino das Despesas",
                options=[a["name"] for a in accounts],
            )
            chosen_account = next(a for a in accounts if a["name"] == selected_acc_name)
        with col_cfg2:
            pdf_file = st.file_uploader(
                "Selecione o arquivo PDF da fatura", type=["pdf"]
            )

        # Inicializa estado da sessão para os itens extraídos e histórico do chat
        if "invoice_items" not in st.session_state:
            st.session_state["invoice_items"] = []
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        if "last_processed_file" not in st.session_state:
            st.session_state["last_processed_file"] = None

        pdf_password = None
        is_encrypted = False
        pdf_bytes = None

        if pdf_file is not None:
            pdf_bytes = pdf_file.read()
            pdf_file.seek(0)
            try:
                is_encrypted = check_pdf_encrypted(pdf_bytes)
            except Exception:  # noqa: BLE001
                is_encrypted = False

            if is_encrypted:
                st.info("🔒 Este arquivo PDF está protegido por senha.")
                pdf_password = st.text_input(
                    "Digite a senha para abrir a fatura (ex: primeiros dígitos do CPF, etc.)",
                    type="password",
                    key=f"pdf_pwd_{pdf_file.name}",
                )

        # Só processa se não for criptografado OU se a senha tiver sido preenchida
        can_process = pdf_file is not None and (not is_encrypted or bool(pdf_password))
        process_key = f"{pdf_file.name}:{pdf_password}" if pdf_file else None

        if can_process and st.session_state["last_processed_file"] != process_key:
            with st.spinner("Lendo arquivo PDF e extraindo compras com OpenAI..."):
                try:
                    raw_text = extract_text_from_pdf(pdf_bytes, password=pdf_password)
                    parsed_container = parse_invoice_with_openai(
                        raw_text, categories=category_names
                    )
                    items_dicts = [item.model_dump() for item in parsed_container.items]
                    st.session_state["invoice_items"] = items_dicts
                    st.session_state["last_processed_file"] = process_key
                    st.session_state["chat_history"] = [
                        {
                            "role": "assistant",
                            "content": f"Encontrei **{len(items_dicts)} despesas** na fatura! Você pode me pedir para filtrar (ex: *'remova compras do iFood'* ou *'mantenha só gastos acima de R$ 50'*), mudar categorias ou tirar dúvidas.",
                        }
                    ]
                    st.success(
                        f"Fatura processada com sucesso! {len(items_dicts)} despesas encontradas."
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Erro ao processar fatura: {exc}")

        items = st.session_state["invoice_items"]

        if items:
            total_invoice = sum(float(i["amount"]) for i in items)
            m1, m2 = st.columns(2)
            m1.metric("Total da Fatura (Itens Atuais)", format_currency(total_invoice))
            m2.metric("Quantidade de Despesas", len(items))

            st.divider()

            # Seção de Chat Interativo
            st.subheader("💬 Chat Interativo de Refinamento e Filtro")
            st.caption(
                "Converse com a IA para ajustar a lista antes de efetivar os lançamentos."
            )

            for msg in st.session_state["chat_history"]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            user_query = st.chat_input(
                "Ex: Desconsidere gastos de farmácia, ou agrupe compras por categoria..."
            )
            if user_query:
                st.session_state["chat_history"].append(
                    {"role": "user", "content": user_query}
                )
                with st.spinner("Processando solicitação com IA..."):
                    try:
                        updated_items, reply = refine_items_with_chat(
                            current_items=st.session_state["invoice_items"],
                            user_message=user_query,
                            categories=category_names,
                        )
                        st.session_state["invoice_items"] = updated_items
                        st.session_state["chat_history"].append(
                            {"role": "assistant", "content": reply}
                        )
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Erro no chat: {exc}")

            st.divider()

            # Tabela e Seleção Final para Importação
            st.subheader("📋 Lançamentos a Importar")
            st.caption(
                "Confira os lançamentos abaixo. Marque ou desmarque os que deseja cadastrar no sistema."
            )

            df_import = []
            for idx, item in enumerate(items):
                inst_text = "À vista"
                if item.get("installment_current") and item.get("installment_total"):
                    inst_text = (
                        f"{item['installment_current']}/{item['installment_total']}"
                    )

                df_import.append(
                    {
                        "Importar": True,
                        "Data": item["date"],
                        "Descrição": item["description"],
                        "Valor": float(item["amount"]),
                        "Categoria": item.get("category_suggestion") or "Outros",
                        "Parcela": inst_text,
                    }
                )

            edited_df = st.data_editor(
                pd.DataFrame(df_import),
                width="stretch",
                hide_index=True,
                column_config={
                    "Importar": st.column_config.CheckboxColumn(
                        "Importar?", default=True
                    ),
                    "Valor": st.column_config.NumberColumn(
                        "Valor (R$)", format="R$ %.2f"
                    ),
                },
            )

            if st.button("🚀 Confirmar e Lançar Despesas Selecionadas", type="primary"):
                selected_rows = edited_df[edited_df["Importar"] == True]
                if selected_rows.empty:
                    st.warning("Nenhum lançamento selecionado para importação.")
                else:
                    success_count = 0
                    errors = []

                    with st.spinner(f"Importando {len(selected_rows)} despesas..."):
                        for _, row in selected_rows.iterrows():
                            # Resolver ID da categoria se existir
                            cat_id = None
                            matched_cat = next(
                                (
                                    c
                                    for c in categories
                                    if c["name"].lower()
                                    == str(row["Categoria"]).lower()
                                ),
                                None,
                            )
                            if matched_cat:
                                cat_id = UUID(matched_cat["id"])

                            val_str = f"{row['Valor']:.2f}"
                            res = UIService.record_transaction(
                                amount=val_str,
                                transaction_type=TransactionType.EXPENSE,
                                source_account_id=UUID(chosen_account["id"]),
                                category_id=cat_id,
                                description=str(row["Descrição"]),
                                transaction_date=f"{row['Data']}T12:00:00Z",
                                total_installments=1,
                            )
                            if "error" in res:
                                errors.append(
                                    f"{row['Descrição']}: {res['error']['message']}"
                                )
                            else:
                                success_count += 1

                    if errors:
                        st.error("Alguns erros ocorreram:\n" + "\n".join(errors))
                    if success_count > 0:
                        st.success(
                            f"{success_count} despesas foram importadas com sucesso na conta {chosen_account['name']}!"
                        )
                        # Limpa estado da fatura
                        st.session_state["invoice_items"] = []
                        st.session_state["chat_history"] = []
                        st.session_state["last_processed_file"] = None
                        st.rerun()
        else:
            st.info("Envie um arquivo PDF de fatura acima para iniciar.")

    # -------------------------------------------------------------
    # 4. ASSISTENTE FINANCEIRO (CHAT)
    # -------------------------------------------------------------
    elif menu == "💬 Assistente Financeiro":
        st.title("💬 Assistente Financeiro")
        st.caption(
            "Converse em linguagem natural sobre suas finanças. "
            "Pergunte saldos, extratos, orçamentos ou peça para registrar uma transação."
        )

        # Sidebar extras
        if st.sidebar.button("🗑️ Limpar Conversa", key="btn_clear_chat"):
            st.session_state["financial_chat_history"] = []
            st.session_state["financial_pending_action"] = None
            st.rerun()

        # Session state initialisation
        if "financial_chat_history" not in st.session_state:
            st.session_state["financial_chat_history"] = []
        if "financial_pending_action" not in st.session_state:
            st.session_state["financial_pending_action"] = None

        chat_history: list[dict] = st.session_state["financial_chat_history"]
        pending: PendingAction | None = st.session_state["financial_pending_action"]

        # Render chat history
        for msg in chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Confirmation block for pending write actions
        if pending is not None:
            with st.container(border=True):
                st.warning("⚠️ **Confirme a ação abaixo antes de efetivar:**")
                st.markdown(pending.summary)
                col_ok, col_cancel, _ = st.columns([1, 1, 4])
                with col_ok:
                    if st.button(
                        "✅ Confirmar", type="primary", key="btn_confirm_pending"
                    ):
                        with st.spinner("Registrando transação..."):
                            result = execute_pending_action(pending)
                        if "error" in result:
                            st.error(
                                f"Erro ao registrar: {result['error'].get('message', result['error'])}"
                            )
                        else:
                            st.success("Transação registrada com sucesso!")
                            chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": "✅ Transação registrada com sucesso! Posso ajudar com mais alguma coisa?",
                                }
                            )
                        st.session_state["financial_pending_action"] = None
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancelar", key="btn_cancel_pending"):
                        chat_history.append(
                            {
                                "role": "assistant",
                                "content": "Tudo bem, o lançamento foi cancelado. Posso ajudar com mais alguma coisa?",
                            }
                        )
                        st.session_state["financial_pending_action"] = None
                        st.rerun()

        # Chat input
        user_input = st.chat_input(
            "Ex: Qual meu saldo total? / Lance R$ 80 de supermercado na Nubank / Como estão meus orçamentos?"
        )
        if user_input:
            chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"), st.spinner("Pensando..."):
                try:
                    reply, new_pending = chat_with_financial_assistant(
                        messages=chat_history,
                    )
                    st.markdown(reply)
                    chat_history.append({"role": "assistant", "content": reply})
                    st.session_state["financial_pending_action"] = new_pending
                except Exception as exc:  # noqa: BLE001
                    err_msg = f"Erro ao consultar o assistente: {exc}"
                    st.error(err_msg)
                    chat_history.append({"role": "assistant", "content": err_msg})

            st.session_state["financial_chat_history"] = chat_history
            if st.session_state["financial_pending_action"] is not None:
                st.rerun()

    # -------------------------------------------------------------
    # 5. ORÇAMENTOS & METAS
    # -------------------------------------------------------------
    elif menu == "🎯 Orçamentos & Metas":
        st.title("🎯 Acompanhamento Orçamentário")

        now = datetime.now(UTC)
        col_m, col_y = st.columns(2)
        with col_m:
            mes = st.selectbox(
                "Mês de Referência", list(range(1, 13)), index=now.month - 1
            )
        with col_y:
            ano = st.number_input("Ano", min_value=2020, max_value=2030, value=now.year)

        status_data = UIService.get_budget_status(month=mes, year=ano)
        summary = status_data.get("summary", {})
        budgets = status_data.get("budgets", [])

        # Resumo Orçamentário
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Total Previsto", format_currency(summary.get("total_budgeted", "0.00"))
        )
        c2.metric("Total Gasto", format_currency(summary.get("total_spent", "0.00")))
        c3.metric(
            "Saldo Restante", format_currency(summary.get("total_remaining", "0.00"))
        )
        c4.metric("% Consumido", f"{float(summary.get('overall_percentage', 0)):.1f}%")

        st.divider()

        st.subheader("📊 Metas por Categoria")
        if budgets:
            for b in budgets:
                with st.container(border=True):
                    col_cat, col_val = st.columns([3, 1])
                    with col_cat:
                        st.markdown(f"### {b['category_name']}")
                        pct = float(b["spent_percentage"])
                        prog = min(pct / 100.0, 1.0)
                        st.progress(prog)
                        if b["is_exceeded"]:
                            st.error(
                                f"⚠️ Limite estourado em {format_currency(abs(float(b['remaining_balance'])))} ({pct:.1f}% consumido)"
                            )
                        else:
                            st.caption(
                                f"{pct:.1f}% consumido — Restam {format_currency(b['remaining_balance'])}"
                            )
                    with col_val:
                        st.metric("Limite", format_currency(b["budget_amount"]))
                        st.metric("Gasto", format_currency(b["spent_amount"]))
        else:
            st.info("Nenhum orçamento cadastrado para este mês.")

        # Formulário para Definir/Atualizar Orçamento
        st.subheader("➕ Definir ou Atualizar Orçamento")
        categories_data = UIService.list_categories(category_type="expense")
        expense_cats = categories_data.get("categories", [])

        if expense_cats:
            with st.form("form_budget"):
                b_cat_name = st.selectbox(
                    "Categoria de Despesa", [c["name"] for c in expense_cats]
                )
                b_val = st.text_input("Limite Mensal (R$)", placeholder="ex: 600.00")
                if st.form_submit_button("Salvar Orçamento", type="primary"):
                    try:
                        cat_obj = next(
                            c for c in expense_cats if c["name"] == b_cat_name
                        )
                        res = UIService.set_budget(
                            category_id=UUID(cat_obj["id"]),
                            amount=b_val,
                            month=mes,
                            year=ano,
                        )
                        if "error" in res:
                            st.error(f"Erro: {res['error']['message']}")
                        else:
                            st.success("Orçamento salvo com sucesso!")
                            st.rerun()
                    except (ValueError, KeyError, TypeError) as exc:
                        st.error(f"Erro: {exc}")

    # -------------------------------------------------------------
    # 4. CONFIGURAÇÕES
    # -------------------------------------------------------------
    elif menu == "⚙️ Configurações":
        st.title("⚙️ Gerenciamento de Contas e Categorias")

        col_new_acc, col_new_cat = st.columns(2)

        with col_new_acc, st.container(border=True):
            st.subheader("🏦 Cadastrar Nova Conta")
            with st.form("form_new_acc"):
                acc_name = st.text_input("Nome da Conta", placeholder="ex: Nubank")
                acc_type = st.selectbox(
                    "Tipo de Conta",
                    [
                        AccountType.CHECKING,
                        AccountType.SAVINGS,
                        AccountType.INVESTMENT,
                        AccountType.CASH,
                    ],
                )
                acc_init = st.text_input("Saldo Inicial (R$)", value="0.00")
                if st.form_submit_button("Criar Conta"):
                    res = UIService.create_account(acc_name, acc_type, acc_init)
                    if "error" in res:
                        st.error(f"Erro: {res['error']['message']}")
                    else:
                        st.success(f"Conta '{acc_name}' criada!")
                        st.rerun()

        with col_new_cat, st.container(border=True):
            st.subheader("🏷️ Cadastrar Nova Categoria")
            with st.form("form_new_cat"):
                cat_name = st.text_input("Nome da Categoria", placeholder="ex: Saúde")
                cat_type = st.selectbox(
                    "Tipo", [CategoryType.EXPENSE, CategoryType.INCOME]
                )
                if st.form_submit_button("Criar Categoria"):
                    res = UIService.create_category(cat_name, cat_type)
                    if "error" in res:
                        st.error(f"Erro: {res['error']['message']}")
                    else:
                        st.success(f"Categoria '{cat_name}' criada!")
                        st.rerun()

        st.divider()

        # Gerenciamento e Exclusão de Contas
        st.subheader("🗑️ Gerenciar e Excluir Contas")
        accounts_data = UIService.list_accounts()
        all_accounts = accounts_data.get("accounts", [])

        if not all_accounts:
            st.info("Nenhuma conta cadastrada.")
        else:
            with st.container(border=True):
                st.caption(
                    "Exclua contas sem movimentação ou desative contas existentes para manter seu histórico íntegro."
                )
                acc_options = {
                    f"{a['name']} ({a['account_type'].upper()}) - Saldo: {format_currency(a['balance'])} [{a['id'][:8]}]": a
                    for a in all_accounts
                }
                selected_acc_label = st.selectbox(
                    "Selecione a conta para excluir/desativar",
                    options=list(acc_options.keys()),
                    key="select_acc_delete",
                )

                if selected_acc_label:
                    target_acc = acc_options[selected_acc_label]
                    force_cascade = st.checkbox(
                        "⚠️ Excluir permanentemente do banco junto com todo o histórico de transações (Cascade)",
                        value=False,
                        help="Se desmarcado e a conta tiver movimentações, ela será apenas desativada (soft-delete), preservando seus registros históricos.",
                    )

                    if st.button(
                        "Confirmar Exclusão da Conta",
                        type="primary",
                        key="btn_delete_acc_confirm",
                    ):
                        del_acc_res = UIService.delete_account(
                            account_id=UUID(target_acc["id"]),
                            force_cascade=force_cascade,
                        )
                        if "error" in del_acc_res:
                            st.error(
                                f"Erro ao excluir conta: {del_acc_res['error']['message']}"
                            )
                        else:
                            st.success(
                                del_acc_res.get(
                                    "message", "Conta processada com sucesso!"
                                )
                            )
                            st.rerun()


if __name__ == "__main__":
    main()
