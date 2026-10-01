# Feature Specification: Transações Futuras, Encargos e Projeção de Parcelas na Importação de Faturas (011-invoice-future-transactions-and-charges)

**Feature Branch**: `fix/invoice-table-date-column-type`

**Created**: 2026-09-30

**Status**: Implemented ✅

**Input**: O importador de faturas deve considerar transações futuras (próximas faturas), despesas, tarifas e encargos (juros, multas, IOF), além de oferecer a opção de projetar as parcelas futuras restantes no sistema como pendentes.

---

## Cenários de Usuário & Testes

### User Story 1 — Extração de Despesas, Encargos e Faturas Futuras no PDF (Priority: P1)
Como usuário que importa faturas de cartão de crédito em PDF,  
Quero que o extrator estruturado capture tanto as compras do período quanto tarifas/encargos (IOF, juros, tarifas de anuidade) e transações agendadas para faturas futuras,  
Para que nenhuma cobrança ou previsão financeira fique de fora do meu planejamento.

**Acceptance Scenarios**:
1. **Given** um PDF de fatura contendo seção de "Próximas faturas" ou "Lançamentos futuros", **When** o extrator analisa o texto, **Then** as transações futuras são identificadas com `is_future=True`.
2. **Given** encargos, juros, IOF ou tarifas cobradas na fatura, **When** o extrator executa a leitura, **Then** esses itens são extraídos como despesas com valor monetário positivo, ignorando apenas pagamentos efetuados pelo cliente e totais.
3. **Given** transações pertencentes à fatura atual, **When** extraídas, **Then** possuem `is_future=False`.

---

### User Story 2 — Visualização e Controle na Interface Streamlit (Priority: P1)
Como gestor financeiro na tela de importação de faturas,  
Quero filtrar se desejo visualizar lançamentos de faturas futuras e marcar/desmarcar individualmente a coluna "Fatura Futura?",  
Para ter visibilidade clara e controle granular sobre o que pertence à fatura atual e o que pertence a períodos seguintes.

**Acceptance Scenarios**:
1. **Given** a tela de revisão dos lançamentos da fatura, **When** há despesas futuras extraídas, **Then** o usuário pode alternar a exibição via checkbox "Listar lançamentos de faturas futuras".
2. **Given** os lançamentos exibidos na tabela (`st.data_editor`), **When** visualizados, **Then** uma coluna "Fatura Futura?" permite editar o indicador de cada item.

---

### User Story 3 — Projeção de Parcelas Restantes e Gravação Segura sem Débito Prematuro (Priority: P1)
Como gestor financeiro,  
Quero poder escolher projetar automaticamente as parcelas futuras restantes (ex: de uma compra 2/10, gerar parcelas 3 a 10 nos meses seguintes) e garantir que todas as transações futuras sejam salvas como `pending`,  
Para manter a previsibilidade dos meses seguintes sem que o saldo atual da conta seja reduzido antes do vencimento.

**Acceptance Scenarios**:
1. **Given** transações marcadas como "Fatura Futura", **When** importadas para a conta, **Then** são salvas com `status=TransactionStatus.PENDING`, não debitando o saldo atual.
2. **Given** a opção "Projetar e lançar parcelas futuras restantes como pendentes" ativada, **When** confirmada a importação de uma compra parcelada (ex: parcela 2 de 10), **Then** as parcelas 3 a 10 são geradas automaticamente com datas calculadas mensalmente (`add_months`) e registradas como pendentes.

---

## Requisitos Funcionais & Técnicos

- **RF-001**: O modelo `ExtractedInvoiceItem` DEVE conter o campo `is_future: bool = False`.
- **RF-002**: O prompt do OpenAI em `parse_invoice_with_openai` DEVE instruir a captura de tarifas, IOF, juros, encargos e identificar itens de faturas futuras marcando `is_future=True`.
- **RF-003**: `UIService.record_transaction` DEVE suportar `status` e `installment_number` para viabilizar registros com status `pending` e parcelamento específico.
- **RF-004**: O frontend Streamlit DEVE fornecer toggle para listar transações futuras e checkbox para projeção de parcelas restantes.
- **RF-005**: Transações de faturas futuras e parcelas projetadas DEVEM ser cadastradas com `status=TransactionStatus.PENDING`.

---

## Critérios de Sucesso

- **CS-001**: O usuário consegue visualizar encargos, despesas e transações futuras extraídas do PDF na tabela de importação.
- **CS-002**: As transações futuras são salvas com status pendente, garantindo saldo inalterado.
- **CS-003**: A opção de projetar parcelas restantes gera os registros pendentes corretos para os meses seguintes.
- **CS-004**: 100% dos testes unitários e de integração das rotinas de parsing e transações passam com sucesso.
