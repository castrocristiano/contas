from datetime import UTC, datetime, timedelta
from uuid import UUID

import pandas as pd
import streamlit as st

from contas.models.account import AccountType
from contas.models.category import CategoryType
from contas.models.transaction import TransactionType
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
                        pd.DataFrame(df_data), use_container_width=True, hide_index=True
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
    # 3. ORÇAMENTOS & METAS
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


if __name__ == "__main__":
    main()
