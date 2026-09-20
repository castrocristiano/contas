# Feature Specification: Leitura de Fatura PDF com Chat Interativo e Lançamento (005-invoice-pdf-chat)

**Feature Branch**: `feature/005-invoice-pdf-chat`

**Created**: 2026-09-19

**Status**: Draft

**Input**: Leitura de PDF de fatura de cartão de crédito, filtro interativo via chat, e cadastro no sistema.

---

## User Scenarios & Testing

### User Story 1 - Upload de Fatura PDF e Extração Estruturada com OpenAI (Priority: P1) 🎯 MVP

Como usuário do sistema Contas,  
Quero fazer o upload do PDF da fatura do meu cartão de crédito e ter todas as despesas extraídas automaticamente com precisão,  
Para que eu não precise digitar manualmente cada compra realizada no mês.

**Why this priority**: É a fundação do processamento automatizado de faturas.

**Independent Test**: Fazer upload de um arquivo PDF contendo compras com data, descrição, valor e parcelas; o extrator processa o documento e retorna a lista estrita de itens mapeados.

**Acceptance Scenarios**:
1. **Given** um arquivo PDF de fatura válido, **When** o usuário submete o arquivo na interface, **Then** o sistema extrai o texto do PDF e utiliza a OpenAI (com Structured Outputs / Pydantic) para mapear data, descrição, valor (em Decimal exato) e indicador de parcela (ex: 02/10).
2. **Given** um PDF ilegível ou vazio, **When** o upload é realizado, **Then** o sistema exibe mensagem amigável de erro orientando o usuário.

---

### User Story 2 - Chat Interativo para Filtragem e Refinamento de Lançamentos (Priority: P2)

Como usuário,  
Quero conversar em linguagem natural com um assistente de chat sobre os itens extraídos da fatura (ex: "remova compras de supermercado", "filtre apenas gastos acima de R$ 50", "categorize 'Uber' como Transporte"),  
Para que eu possa ajustar rapidamente quais transações serão lançadas e como devem ser categorizadas antes de persistir.

**Why this priority**: Dá ao usuário total controle e flexibilidade de forma conversacional e intuitiva.

**Independent Test**: Digitar comandos em linguagem natural no chat e verificar que a lista filtrada/revisada de transações em exibição reflete imediatamente os filtros e categorizações solicitados.

**Acceptance Scenarios**:
1. **Given** uma lista de 20 transações extraídas, **When** o usuário digita "desconsidere as compras do iFood", **Then** as compras do iFood são desmarcadas/removidas da seleção de importação.
2. **Given** comandos de agregação ou dúvidas como "quanto gastei no total de alimentação?", **When** perguntado no chat, **Then** o assistente responde com os valores consolidados.

---

### User Story 3 - Cadastro e Efetivação das Transações no Banco de Dados (Priority: P3)

Como gestor das finanças,  
Quero selecionar a conta de destino (cartão de crédito / conta corrente) e confirmar a importação dos lançamentos filtrados com um clique,  
Para que todos os registros sejam salvos atomicamente no banco de dados e reflitam no saldo e extrato do sistema.

**Why this priority**: Fecha o ciclo de ponta a ponta garantindo integridade financeira e persistência confiável.

**Independent Test**: Clicar em "Confirmar Importação de Transações" e verificar que as transações selecionadas foram criadas no banco de dados via `record_transaction`, com parcelas identificadas corretamente.

**Acceptance Scenarios**:
1. **Given** itens revisados e confirmados, **When** o usuário clica em "Importar Selecionados", **Then** cada transação é persistida chamando a ferramenta de transações, vinculada à conta e categoria corretas.
2. **Given** transações com parcelamento indicado no PDF (ex: 3/10), **When** importadas, **Then** o sistema registra os metadados de parcela (`installment_number=3`, `total_installments=10`).

