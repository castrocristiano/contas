# Feature Specification: Compras Parceladas (003-installment-purchases)

**Feature Branch**: `feature/003-installment-purchases`

**Created**: 2026-09-19

**Status**: Draft

**Input**: User description: "Quero adicionar uma feature para quando for uma compra parcelada, tenha o número de parcelas, a parcela atual e o total, com geração automática de parcelas e vínculo único da compra."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registro de Despesa Parcelada com Projeção Automática (Priority: P1) 🎯 MVP

Como gestor das finanças domésticas,
Quero registrar uma despesa informando o total de parcelas (ex: 10x de R$ 120,00 ou valor total de R$ 1.200,00 em 10x),
Para que o sistema debite a primeira parcela imediatamente e agende automaticamente as demais parcelas futuras no extrato.

**Why this priority**: É a funcionalidade central. Compras parceladas representam grande parte das despesas em cartões de crédito e faturas familiares, permitindo previsão orçamentária realista.

**Independent Test**: Pode ser testado registrando uma compra de R$ 300,00 em 3x em uma conta. O sistema deve criar 3 transações vinculadas: a 1ª com status `cleared` na data informada, e a 2ª e 3ª com status `pending` espaçadas de 1 mês cada, todas marcadas com `current_installment`, `total_installments`, `total_amount` e o mesmo identificador de parcelamento (`installment_id`).

**Acceptance Scenarios**:
1. **Given** uma conta com saldo de R$ 1.000,00, **When** o usuário registra uma compra de R$ 300,00 em 3 parcelas de R$ 100,00 na data 2026-09-19, **Then** a parcela 1/3 (R$ 100,00) é liquidada imediatamente (`cleared`), reduzindo o saldo da conta para R$ 900,00, e as parcelas 2/3 (2026-10-19) e 3/3 (2026-11-19) são registradas com status `pending` sem afetar o saldo liquidado da conta.
2. **Given** uma compra com valor total não divisível perfeitamente (ex: R$ 100,00 em 3x), **When** o sistema gera as parcelas, **Then** a soma das parcelas deve ser estritamente igual ao valor total informado (ex: 33,34 na primeira parcela e 33,33 nas restantes duas, utilizando aritmética `Decimal` exata).

---

### User Story 2 - Consulta e Visualização de Parcelas em Extratos (Priority: P2)

Como usuário consultando o extrato financeiro,
Quero identificar visualmente quais despesas são parceladas, qual é a parcela corrente (ex: "2/10") e o valor total da compra original,
Para que eu tenha clareza do compromisso financeiro ao auditar meus lançamentos.

**Why this priority**: Complementa o extrato com transparência sobre os compromissos assumidos.

**Independent Test**: Pode ser testado executando `get_statement` incluindo pendências (`include_pending=True`) e validando que os itens retornados apresentam os campos `installment_number`, `total_installments`, `total_amount` e `installment_id`.

**Acceptance Scenarios**:
1. **Given** transações com metadados de parcelamento registradas, **When** o usuário solicita o extrato via `get_statement`, **Then** as transações parceladas trazem os detalhes de parcelamento no retorno.

---

### User Story 3 - Consulta Consolidada do Plano de Parcelamento (Priority: P3)

Como usuário planejando o orçamento dos próximos meses,
Quero consultar o status de uma compra parcelada pelo seu identificador ou listar todos os planos de compras parceladas ativas,
Para saber quantas parcelas faltam pagar e qual o montante devedor futuro remanescente.

**Why this priority**: Oferece previsibilidade patrimonial de médio e longo prazo sobre dívidas ativas.

**Independent Test**: Chamar `get_installment_plan` fornecendo o identificador da compra parcelada e receber o resumo: total pago, total restante, parcelas quitadas e pendentes.

**Acceptance Scenarios**:
1. **Given** uma compra parcelada em 5x de R$ 200,00 com 2 parcelas já liquidadas, **When** o usuário consulta o plano de parcelamento, **Then** o sistema retorna total original R$ 1.000,00, montante pago R$ 400,00, saldo remanescente R$ 600,00, e as 3 parcelas pendentes.

---

### Edge Cases

- **Virada de ano e dias finais do mês (31 -> 28/30)**: Ao calcular datas para parcelas subsequentes em meses de 28, 29 ou 30 dias (ex: compra no dia 31 de janeiro), o sistema deve ajustar para o último dia válido do mês subsequente (28 de fevereiro, 31 de março, 30 de abril) sem causar erro de calendário.
- **Compra de 1x**: Se o usuário registrar compra parcelada com `total_installments = 1`, o sistema aceita como transação simples sem gerar parcelas futuras pendentes.
- **Divisão com restos fracionários de centavos**: A diferença de arredondamento de centavos (`amount - sum(parcelas_arredondadas)`) deve ser compensada na primeira parcela para garantir invariância contábil estrita (`Decimal`).
- **Validação de entradas**: Rejeitar `total_installments < 1`, `current_installment < 1` ou `current_installment > total_installments`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE permitir informar metadados de parcelamento ao registrar uma transação: `total_installments` (inteiro >= 1), `installment_number` (inteiro >= 1), `total_amount` (Decimal positivo) e `installment_id` (UUID único de agrupamento).
- **FR-002**: O sistema DEVE gerar automaticamente as parcelas futuras com status `pending` quando `total_installments > 1` e `installment_number == 1` na ferramenta de registro de transações.
- **FR-003**: O sistema DEVE calcular as datas das parcelas subsequentes com incremento mensal seguro preservando o dia do mês (ou último dia válido do mês quando o mês não tiver o dia correspondente).
- **FR-004**: O sistema DEVE garantir que o somatório exato de todas as parcelas geradas seja matematicamente idêntico ao `total_amount` informado, alocando qualquer resíduo fracionário de centavos na primeira parcela.
- **FR-005**: O sistema DEVE expor no extrato (`get_statement`) as informações de parcelamento (`installment_number`, `total_installments`, `total_amount`, `installment_id`).
- **FR-006**: O sistema DEVE disponibilizar uma ferramenta MCP `get_installment_plan` para consultar o progresso, total pago, total a vencer e lista de parcelas de uma compra parcelada.
- **FR-007**: Todas as parcelas geradas DEVEM herdar a mesma conta (`source_account_id`), mesma categoria (`category_id`) e mesma moeda.

### Key Entities

- **Transaction**:
  - `installment_id: UUID | None` (identificador único compartilhado por todas as parcelas da mesma compra)
  - `installment_number: int | None` (número da parcela atual, 1 a N)
  - `total_installments: int | None` (total de parcelas da compra, N >= 1)
  - `total_amount: Decimal | None` (valor total da compra integral)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das compras parceladas dividem o valor com precisão de centavos sem qualquer perda ou acréscimo de valor (`sum(installments) == total_amount`).
- **SC-002**: Todas as parcelas futuras são agendadas em datas cronologicamente válidas, mesmo em compras feitas nos dias 29, 30 ou 31.
- **SC-003**: Consulta de extrato com `include_pending=True` apresenta imediatamente as parcelas futuras programadas.

---

## Assumptions

- Compras parceladas ocorrem primordialmente em periodicidade mensal.
- A primeira parcela é liquidada imediatamente no registro (`cleared`), debitando o saldo da conta, enquanto as parcelas 2..N são salvas como `pending`, não alterando o saldo liquidado até sua data de liquidação.
- O usuário pode informar o valor total da compra (`total_amount`) e o número de parcelas, calculando-se o valor de cada parcela automaticamente, ou fornecer o valor da parcela individualmente validando a coerência.

