# Feature Specification: Filtros de Quitação e Saldo Projetado no Dashboard e Extratos (023-settlement-filters)

**Feature Branch**: `feature/023-settlement-filters`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "vamos criar uma nova feature, em dashboar e extratos, vamos criar filtros para abater do saldo já quitadas, não exibir já quitadas"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filtragem por Status de Quitação no Extrato de Movimentações (Priority: P1) 🎯 MVP

Como usuário do sistema de gestão financeira,
Quero poder filtrar as movimentações do extrato por status de quitação ("Todas", "Apenas Pendentes / Não Quitadas" e "Apenas Quitadas"),
Para que eu consiga identificar rapidamente quais despesas/receitas ainda estão em aberto para pagamento/recebimento, sem a poluição visual de lançamentos já liquidados.

**Why this priority**: É a necessidade operacional mais frequente do usuário ao conferir o extrato bancário ou faturas: isolar as contas do mês que ainda não foram pagas para planejar os pagamentos imediatos.

**Independent Test**: Pode ser testado acessando o Extrato de qualquer conta com transações mistas (quitadas e pendentes), selecionando a opção "Apenas Pendentes" e verificando se todas as transações exibidas na tabela possuem status pendente, e o resumo financeiro (receitas, despesas, resultado líquido) reflete apenas as transações filtradas.

**Acceptance Scenarios**:
1. **Given** que o usuário está visualizando o extrato de uma conta com movimentações quitadas e pendentes, **When** seleciona o filtro "Apenas Pendentes (ocultar quitadas)", **Then** a tabela de transações oculta todos os lançamentos quitados, exibindo estritamente os pendentes, e o card de resumo financeiro atualiza os totais considerando apenas esses itens.
2. **Given** que o usuário deseja auditar o que já foi efetivamente pago/recebido no período, **When** seleciona o filtro "Apenas Quitadas", **Then** a tabela exibe unicamente as transações liquidadas, ocultando parcelas futuras e pendências.
3. **Given** que o usuário deseja visualizar o histórico completo tradicional, **When** seleciona a opção "Todas", **Then** o extrato exibe tanto transações quitadas quanto pendentes (respeitando o checkbox de incluir parcelas futuras).

---

### User Story 2 - Visão Comparativa de Saldo Atual vs. Saldo Projetado no Dashboard (Priority: P2)

Como usuário gerenciando o orçamento familiar/residencial,
Quero visualizar no Dashboard tanto o meu Saldo Atual (realizado, já considerando o que foi quitado) quanto o Saldo Projetado (abatendo despesas pendentes e somando receitas pendentes no período),
Para que eu saiba exatamente quanto dinheiro resta disponível após honrar todos os compromissos financeiros em aberto.

**Why this priority**: Permite antecipar se haverá saldo suficiente na conta até o final do mês/período sem exigir cálculos manuais fora do sistema.

**Independent Test**: Pode ser testado cadastrando um saldo inicial de conta (ex: R$ 1.000,00) e despesas pendentes no mês (ex: R$ 300,00); ao alternar ou visualizar a métrica de saldo projetado, o valor exibido deve ser de R$ 700,00, mantendo o saldo atual em R$ 1.000,00.

**Acceptance Scenarios**:
1. **Given** contas cadastradas com transações pendentes no mês corrente, **When** o usuário consulta o Dashboard, **Then** o sistema exibe os saldos por conta com distinção clara entre "Saldo Atual" (realizado em conta) e "Saldo Projetado" (abatendo despesas pendentes e somando receitas pendentes).
2. **Given** o card de "Patrimônio Total" no topo do Dashboard, **When** o usuário ativa a visualização projetada ou confere os indicadores, **Then** o total consolidado apresenta tanto o patrimônio líquido atual quanto o saldo total projetado após a liquidação das pendências do período.
3. **Given** uma conta sem nenhuma movimentação pendente para o período, **When** a métrica projetada é calculada, **Then** o Saldo Projetado é idêntico ao Saldo Atual.

---

### User Story 3 - Filtro Rápido ou Alternador no Dashboard para Exclusão de Pendências (Priority: P3)

Como usuário consultando a saúde financeira no Dashboard,
Quero dispor de um controle rápido de seleção de visão ("Saldo Atual / Realizado", "Saldo Projetado" ou "Apenas Pendências a Vencer"),
Para focar na informação relevante para a minha tomada de decisão no momento da navegação.

**Why this priority**: Melhora a usabilidade e a ergonomia da interface, evitando sobrecarga cognitiva e permitindo focar alternadamente no momento presente ou no futuro próximo.

**Independent Test**: Pode ser testado acionando o seletor no Dashboard e verificando a atualização reativa dos cards de saldos e gráficos sem recarregar a página desnecessariamente.

**Acceptance Scenarios**:
1. **Given** o Dashboard carregado, **When** o usuário seleciona a visão "Apenas Pendências a Vencer", **Then** os cards de contas destacam o montante de compromissos pendentes a serem pagos por conta no mês.
2. **Given** a alternância de visões, **When** o usuário seleciona "Saldo Projetado", **Then** todas as métricas financeiras de contas e patrimônio passam a exibir os valores líquidos projetados.

---

### Edge Cases

- **Conta com saldo projetado negativo**: O sistema deve indicar visualmente (ex: cor de destaque / alerta amigável) quando o abatimento das despesas pendentes resultar em saldo projetado negativo, alertando o usuário sobre risco de insuficiência de fundos.
- **Transferências pendentes entre contas do próprio usuário**: Ao calcular o saldo projetado, uma transferência pendente deve abater da conta de origem e somar na conta de destino, mantendo a consistência do patrimônio consolidado.
- **Transações pendentes com vencimentos em períodos distantes**: O cálculo do saldo projetado deve respeitar um horizonte temporal padrão bem delimitado (ex: até o final do mês corrente ou data configurável), evitando que parcelas de 12 meses futuros distorçam o saldo imediato.
- **Conta inativa com lançamentos pendentes**: Apenas contas ativas devem ser consideradas no cálculo do saldo projetado padrão no Dashboard, a menos que o filtro de contas inativas esteja explicitamente ativado.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE adicionar no Extrato de Movimentações um seletor de status de quitação com 3 opções mutuamente exclusivas:
  - `Todas`: exibe todas as movimentações do período especificado.
  - `Apenas Pendentes`: exibe unicamente movimentações com status `pending` (ocultando as já quitadas).
  - `Apenas Quitadas`: exibe unicamente movimentações com status `cleared` (ocultando as pendentes).
- **FR-002**: A API / caso de uso de extrato (`GetStatementUseCase` e schema `GetStatementInput`) DEVE aceitar um parâmetro opcional de filtro por status (`status: TransactionStatus | None` ou string correspondente `all`, `cleared`, `pending`).
- **FR-003**: Os totais resumidos do extrato (receitas, despesas e resultado líquido) DEVEM ser recalculados com precisão decimal exata com base estrita nas transações filtradas pelo status selecionado.
- **FR-004**: O Dashboard DEVE fornecer a métrica de "Saldo Projetado" por conta e consolidada, calculada a partir da fórmula determinística:
  $$\text{Saldo Projetado} = \text{Saldo Atual} + \sum \text{Receitas Pendentes} - \sum \text{Despesas Pendentes} - \sum \text{Transferências Enviadas Pendentes} + \sum \text{Transferências Recebidas Pendentes}$$
- **FR-005**: O Dashboard DEVE oferecer um seletor ou exibição integrada permitindo ao usuário conferir o Saldo Atual (realizado / liquidadas), o Saldo Projetado (após pendências) e o Total de Pendências a Liquidar no mês de referência.
- **FR-006**: Todos os cálculos monetários de saldos e projeções DEVEM utilizar representação decimal exata (`Decimal`), em conformidade estrita com a Constituição do Contas (Princípio II).
- **FR-007**: A seleção em lote e ações do extrato (ex: "Liquidar Lançamentos" ou "Excluir") DEVEM operar normalmente sobre os itens visíveis filtrados, respeitando as seleções do usuário.

---

### Key Entities *(include if feature involves data)*

- **Account**: Entidade de conta financeira contendo `balance` (saldo atual realizado), `account_type`, `is_active` e agora com cálculo de suporte a `projected_balance`.
- **Transaction**: Entidade de lançamento contendo `amount`, `transaction_type` (`income`, `expense`, `transfer`), `status` (`cleared`, `pending`), `due_date` e contas envolvidas.
- **StatementFilter**: Objeto de parâmetros de consulta ao extrato contendo `account_id`, `start_date`, `end_date`, `date_type`, `status_filter` (`all`, `cleared`, `pending`) e `search`.
- **AccountBalanceProjection**: Estrutura contendo `account_id`, `current_balance`, `pending_income`, `pending_expense`, `projected_balance` e `period_end_date`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O usuário consegue visualizar no Extrato apenas transações não quitadas com 1 clique no seletor de status, sem necessidade de recarregar a aplicação ou navegar para outra tela.
- **SC-002**: 100% dos cálculos de Saldo Projetado e resumos por status refletem matematicamente as pendências cadastradas sem discrepância de centavos.
- **SC-003**: O tempo de renderização do Dashboard e do Extrato com o filtro de status aplicado não excede o tempo atual de resposta em mais de 10%.
- **SC-004**: O usuário identifica com clareza visual imediata o impacto das despesas pendentes sobre o seu saldo disponível antes do vencimento das obrigações.

---

## Assumptions

- O status das transações no banco continua sendo estritamente `cleared` ou `pending`, conforme definido no modelo relacional existente (`TransactionStatus`).
- No Dashboard, o horizonte padrão para projeção de pendências considera as obrigações e recebíveis até o final do mês corrente (ou até a data máxima das despesas do ciclo atual).
- A interface Streamlit refletirá as alterações de forma reativa através de `st.selectbox` / `st.radio` e componentes visuais nativos existentes.
