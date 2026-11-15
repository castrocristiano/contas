# Quickstart & Guia de Validação: Filtros de Quitação e Saldo Projetado (023-settlement-filters)

Este documento descreve os passos práticos para validar e testar a funcionalidade de ponta a ponta.

---

## 1. Pré-Requisitos

1. Ambiente de desenvolvimento configurado com Python 3.12+ e `uv`.
2. Banco de dados PostgreSQL ativo (via `podman-compose up -d db` ou container local).
3. Dependências instaladas (`uv sync`).

---

## 2. Cenário de Validação 1: Filtro de Quitação no Extrato

### Objetivo
Comprovar que o extrato isola corretamente as transações com base no status selecionado e recalcula o sumário com precisão decimal.

### Passos
1. Execute a suíte de testes unitários do caso de uso de extrato:
   ```bash
   .venv/bin/pytest tests/unit/use_cases/test_get_statement_status_filter.py -v
   ```
2. Inicie a interface Streamlit localmente:
   ```bash
   .venv/bin/streamlit run src/contas/ui/app.py
   ```
3. Acesse o menu **"📊 Dashboard & Extrato"**.
4. No extrato da conta selecionada:
   - Alterne o seletor para **"Apenas Pendentes (ocultar quitadas)"**:
     - **Resultado esperado**: Somente movimentações com status "Pendente" são renderizadas na tabela; o total de despesas e receitas no topo do extrato passa a somar estritamente essas pendências.
   - Alterne o seletor para **"Apenas Quitadas"**:
     - **Resultado esperado**: Nenhuma movimentação pendente é visível; apenas lançamentos liquidados são apresentados.
   - Alterne para **"Todas as Movimentações"**:
     - **Resultado esperado**: Ambas são listadas normalmente.

---

## 3. Cenário de Validação 2: Saldo Projetado vs. Saldo Atual no Dashboard

### Objetivo
Comprovar que o Dashboard calcula o saldo projetado abatendo as despesas pendentes do saldo bancário atual.

### Passos
1. Execute os testes automatizados de cálculo de projeção:
   ```bash
   .venv/bin/pytest tests/unit/use_cases/test_dashboard_projections.py -v
   ```
2. Na UI do Dashboard:
   - Cadastre ou selecione uma conta com saldo atual de R$ 1.000,00.
   - Crie uma despesa pendente de R$ 250,00 com vencimento para daqui a 5 dias.
   - Crie uma receita pendente de R$ 100,00 para daqui a 3 dias.
   - Na visualização **"🟢 Saldo Atual (Realizado)"**:
     - A conta deve exibir **R$ 1.000,00**.
   - Alterne para **"🔮 Saldo Projetado (Abatendo pendências)"**:
     - O saldo projetado deve exibir exatamente **R$ 850,00** ($1000 + 100 - 250$).
     - O Patrimônio Total no topo deve exibir o consolidado projetado com precisão.

---

## 4. Validação de Formatação e Qualidade de Código

Conforme a Constituição do Contas e as regras do projeto:
```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```
Ambos os comandos devem retornar código de saída `0`.
