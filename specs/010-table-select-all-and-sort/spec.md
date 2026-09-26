# Feature Specification: Selecionar Tudo e Ordenação de Colunas em Tabelas (010-table-select-all-and-sort)

**Feature Branch**: `feature/010-table-select-all-and-sort`

**Created**: 2026-09-25

**Status**: Implemented ✅

**Input**: Todas as tabelas da interface devem possuir a opção de "Selecionar Tudo" (marcar/desmarcar todos os itens) e suporte nativo e explícito a ordenação por coluna (clique no cabeçalho e/ou controles de ordenação).

---

## Cenários de Usuário & Testes

### User Story 1 — Seleção Global e Ordenação no Extrato de Movimentações (Dashboard) (Priority: P1)
Como gestor financeiro,  
Quero poder ordenar as transações por qualquer coluna (Data, Descrição, Categoria, Tipo, Status, Parcela, Valor) e ter opções de seleção (individual e "Selecionar Tudo") na tabela de extrato,  
Para poder analisar movimentações rapidamente e selecionar lançamentos para exclusão ou conferência em lote com um único clique.

**Acceptance Scenarios**:
1. **Given** a tabela de Extrato de Movimentações no Dashboard, **When** o usuário clica no cabeçalho de qualquer coluna (ou no seletor de ordenação), **Then** a tabela reordena os dados de forma crescente/decrescente.
2. **Given** a tabela de Extrato, **When** o usuário marca a caixa "Selecionar Tudo", **Then** todas as linhas visíveis do extrato passam para o estado selecionado.
3. **Given** múltiplos lançamentos selecionados, **When** o usuário clica em "Excluir Selecionados", **Then** todas as transações selecionadas são removidas e seus saldos estornados de acordo.

### User Story 2 — Seleção Global e Ordenação na Importação de Fatura PDF (Priority: P1)
Como usuário que importa faturas de cartão de crédito em PDF,  
Quero poder ordenar as despesas extraídas (por Data, Valor, Categoria, Descrição) e usar um botão/checkbox de "Selecionar Tudo" / "Desmarcar Tudo",  
Para gerenciar facilmente quais compras serão efetivamente registradas nas minhas contas antes da importação.

**Acceptance Scenarios**:
1. **Given** os itens extraídos da fatura PDF exibidos na tabela, **When** o usuário aciona "Selecionar Tudo", **Then** todas as despesas ficam marcadas para importação.
2. **Given** o usuário aciona "Desmarcar Tudo", **Then** todos os checkboxes são desmarcados, permitindo marcar apenas exceções.
3. **Given** a tabela de importação, **When** o usuário clica nos cabeçalhos (Data, Descrição, Categoria, Valor), **Then** a ordenação é aplicada dinamicamente.

### User Story 3 — Seleção Global e Ordenação no Gerenciamento em Lote de Contas (Configurações) (Priority: P1)
Como usuário na aba de Configurações,  
Quero poder ordenar a lista de contas financeiras por Nome, Tipo, Saldo ou Status e dispor de uma opção "Selecionar Tudo",  
Para selecionar rapidamente todas as contas inativas ou um conjunto de contas e realizar a exclusão/desativação em lote.

**Acceptance Scenarios**:
1. **Given** a tabela de Gerenciar e Excluir Contas em Configurações, **When** o usuário marca o checkbox "Selecionar Tudo", **Then** todas as contas da tabela são marcadas na coluna Selecionar.
2. **Given** a tabela de contas, **When** o usuário clica nos cabeçalhos (Nome, Saldo, Tipo, etc.), **Then** os dados são ordenados corretamente.

---

## Requisitos

### Requisitos Funcionais
- **RF-001**: Todas as tabelas interativas (`st.data_editor` / `st.dataframe`) DEVEM suportar ordenação nativa por clique no cabeçalho das colunas.
- **RF-002**: A tabela de Extrato de Movimentações DEVE oferecer controle de "Selecionar Tudo" / seleção múltipla com suporte a ações em lote (como exclusão de transações).
- **RF-003**: A tabela de Importação de Faturas PDF DEVE fornecer controles de "Selecionar Tudo" e "Desmarcar Tudo" antes do editor interativo.
- **RF-004**: A tabela de Exclusão de Contas em Lote em Configurações DEVE fornecer controle de "Selecionar Tudo" / "Desmarcar Tudo".
- **RF-005**: A ordenação das colunas de valores monetários DEVE ordenar por valor numérico real (e não lexicográfico como texto simples).

---

## Critérios de Sucesso
- **CS-001**: O usuário consegue marcar ou desmarcar todas as linhas com 1 clique nas tabelas de Extrato, Fatura PDF e Gerenciamento de Contas.
- **CS-002**: Todas as tabelas permitem ordenação por qualquer coluna com consistência de tipos (data, número, texto).
- **CS-003**: 100% dos testes unitários e de integração continuam passando e novo teste cobre a lógica de seleção/ordenação.
