# Research & Decisões Arquiteturais: Filtros de Quitação e Saldo Projetado (023-settlement-filters)

## Contexto da Pesquisa

A funcionalidade tem como objetivo principal:
1. Permitir a filtragem de transações no extrato bancário por status de quitação (`cleared` vs `pending`), oferecendo uma visão focada em compromissos pendentes ou no histórico já liquidado.
2. Calcular e apresentar no Dashboard a projeção de saldo (`projected_balance`), que abate do saldo atual realizado as despesas/transferências pendentes e soma as receitas pendentes no horizonte do ciclo financeiro (mês corrente).

---

## Decisão 1: Representação e Tratamento do Filtro de Status no Extrato

### Decisão
Introduzir o parâmetro opcional `status_filter` nos schemas `GetStatementInput`, nas assinaturas do caso de uso `GetStatementUseCase`, no MCP Server e no `UIService`. Os valores aceitos serão:
- `"all"` (padrão): retorna todas as transações (mantendo retrocompatibilidade com o checkbox existente `include_pending`).
- `"pending"`: filtra exclusivamente transações onde `status == TransactionStatus.PENDING`.
- `"cleared"`: filtra exclusivamente transações onde `status == TransactionStatus.CLEARED`.

### Racional
- Mantém 100% de retrocompatibilidade com chamadas existentes ao MCP e ao caso de uso.
- Permite que a filtragem ocorra tanto em memória quanto no nível de banco de dados (`WHERE status = :status`), garantindo paginação correta e desempenho O(1) com índice já existente na coluna `status`.
- O recálculo dos totais do extrato (`total_income`, `total_expense`, `net`) já utiliza a lista filtrada de transações com `Decimal`, assegurando que o resumo financeiro reflita com precisão apenas as transações visíveis.

### Alternativas Consideradas
- **Filtrar apenas na camada de apresentação (DataFrame do Streamlit)**:
  - *Rejeitado*: Se o extrato retornar 50 transações com paginação/limite e a maioria for quitada, o usuário veria uma tabela quase vazia de pendências mesmo havendo dezenas de pendências no banco. A filtragem no backend garante que o limite de registros traga as transações do status desejado.

---

## Decisão 2: Modelo Matemático e Arquitetura do Saldo Projetado no Dashboard

### Decisão
Disponibilizar o cálculo de projeção de saldo através de um método dedicado ou extensão de resumo financeiro (`GetFinancialSummaryUseCase` ou `GetAccountProjectionsUseCase`), que recebe o `user_id` e a data de corte (padrão: último dia do mês corrente).

Para cada conta bancária ativa:
$$\text{projected\_balance} = \text{current\_balance} + \text{pending\_income} - \text{pending\_expense} - \text{pending\_transfers\_out} + \text{pending\_transfers\_in}$$

Onde:
- $\text{current\_balance}$: é o saldo já persistido em `Account.balance` (que pela regra do sistema já reflete todas as transações `CLEARED`).
- $\text{pending\_income}$: soma de todas as transações com `transaction_type = INCOME` e `status = PENDING` vinculadas à conta até a data limite.
- $\text{pending\_expense}$: soma de transações com `transaction_type = EXPENSE` e `status = PENDING` da conta de origem.
- $\text{pending\_transfers\_out}$: transferências pendentes onde a conta é a origem (`source_account_id`).
- $\text{pending\_transfers\_in}$: transferências pendentes onde a conta é o destino (`destination_account_id`).

### Racional
- Respeita o Princípio II da Constituição (Integridade e Precisão Financeira): todos os cálculos são realizados estritamente com `Decimal("0.00")`.
- Respeita o Princípio I (Simplicidade e YAGNI): não cria tabelas adicionais no banco nem triggers complexas; calcula a projeção agregando as transações pendentes que já possuem índice por conta e status.
- Mantém o saldo real inviolável: o saldo em `Account.balance` continua sendo a verdade incontestável dos valores conciliados no banco.

### Alternativas Consideradas
- **Armazenar uma coluna `projected_balance` persistida na tabela `account`**:
  - *Rejeitado*: Geraria risco de drift e dessincronização contínua sempre que uma transação pendente fosse editada, cancelada ou atingisse o vencimento. O cálculo sob demanda via agregação é deterministicamente seguro.

---

## Decisão 3: Experiência do Usuário (UX) no Streamlit

### Decisão
1. **Extrato**:
   - Substituir/evoluir o filtro atual por um `st.selectbox` com 3 opções claras em português:
     - `"Todas as Movimentações"` (`"all"`)
     - `"Apenas Pendentes (não quitadas)"` (`"pending"`)
     - `"Apenas Quitadas (liquidadas)"` (`"cleared"`)
   - O checkbox anterior de "Incluir parcelas futuras/pendentes" passa a sincronizar com este seletor, mantendo simplicidade.

2. **Dashboard**:
   - Adicionar no topo da seção de saldos um controle visual (pílula / `st.radio` horizontal):
     - `🟢 Saldo Atual (Realizado)`
     - `🔮 Saldo Projetado (Abatendo pendências)`
   - Na visão "Saldo Atual": exibe os saldos tradicionais das contas e do patrimônio, com um subtítulo/caption indicando o valor projetado.
   - Na visão "Saldo Projetado": os cards exibem o saldo projetado em destaque e alertam com cor vermelha/amarela se alguma conta estiver com projeção negativa para o mês.

---

## Decisão 4: Conformidade com a Constituição do Projeto

| Item da Constituição | Conformidade |
|:---|:---|
| **I. Simplicidade e YAGNI** | Reutilização das estruturas existentes (`TransactionStatus`, `Account`, `StatementSummary`) sem criar abstrações desnecessárias. |
| **II. Precisão Financeira** | Uso obrigatório de `Decimal` em toda a aritmética de saldo projetado e resumos. |
| **III. MCP Declarativo** | Parâmetro `status_filter` adicionado com validação de schema Pydantic v2 e descrição clara para LLMs. |
| **VI. Idioma** | Documentação e UI em PT-BR; código, modelos, queries e testes em EN-US (`status_filter`, `projected_balance`, `pending_income`). |
