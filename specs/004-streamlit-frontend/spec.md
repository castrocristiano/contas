# Feature Specification: Interface Web com Streamlit (004-streamlit-frontend)

**Feature Branch**: `feature/004-streamlit-frontend`

**Created**: 2026-09-19

**Status**: Draft

**Input**: User choice: "Opção D (Streamlit em Python puro)"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dashboard Financeiro Consolidado (Priority: P1) 🎯 MVP

Como usuário do sistema Contas,
Quero acessar uma interface web interativa no navegador exibindo meu patrimônio total, saldos por conta e lançamentos recentes,
Para que eu tenha visibilidade imediata da minha situação financeira sem precisar consultar linha de comando.

**Why this priority**: É o valor central da interface gráfica. Transforma o sistema em uma aplicação visual direta e acessível.

**Independent Test**: Iniciar a aplicação Streamlit via `uv run streamlit run src/contas/ui/app.py`, acessar `http://localhost:8501` e verificar métricas de patrimônio total, lista de contas ativas e tabela de transações recentes.

**Acceptance Scenarios**:
1. **Given** contas e transações existentes no banco de dados, **When** o usuário abre a aplicação no navegador, **Then** o sistema exibe os cards de saldo de cada conta e o patrimônio total consolidado em BRL.
2. **Given** a página principal carregada, **When** o usuário seleciona um período de datas, **Then** a tabela exibe as movimentações financeiras com formatação monetária correta e badges por tipo (`income`, `expense`, `transfer`).

---

### User Story 2 - Formulário Interativo de Lançamentos e Compras Parceladas (Priority: P2)

Como gestor das despesas da casa,
Quero registrar receitas, despesas e compras parceladas diretamente por um formulário na interface web,
Para que eu possa lançar meus gastos diários rapidamente com validação visual imediata.

**Why this priority**: Permite alimentar o sistema de maneira conveniente pelo navegador.

**Independent Test**: Preencher o formulário de nova transação com despesa parcelada em 3x e submeter; o painel deve atualizar o saldo da conta e listar a primeira parcela imediatamente no extrato.

**Acceptance Scenarios**:
1. **Given** o formulário de lançamento aberto, **When** o usuário preenche valor, conta de origem, categoria e ativa a opção de compra parcelada (ex: 3x), **Then** o sistema grava a transação e as parcelas futuras, atualizando o extrato visual na tela.

---

### User Story 3 - Visualização de Metas Orçamentárias e Planos de Parcelamento (Priority: P3)

Como usuário planejando meus gastos,
Quero ver barras de progresso do consumo dos orçamentos mensais por categoria e o status de quitação de compras parceladas,
Para identificar rapidamente quais categorias estão perto de estourar o limite.

**Why this priority**: Proporciona controle preventivo e clareza sobre dívidas parceladas a vencer.

**Independent Test**: Navegar para a aba/seção de Orçamentos, verificar as barras de progresso (verde para dentro do limite, vermelho com alerta para excedido).

**Acceptance Scenarios**:
1. **Given** orçamentos cadastrados para o mês, **When** o usuário consulta a aba de Orçamentos, **Then** o sistema exibe o percentual gasto, saldo restante e alerta visual caso o orçamento esteja excedido.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE fornecer uma aplicação web em Python utilizando a biblioteca **Streamlit**.
- **FR-002**: O sistema DEVE reaproveitar diretamente a camada de dados e serviços já implementados (`SQLModel`, schemas Pydantic e queries assíncronas/síncronas de sessão).
- **FR-003**: A interface DEVE exibir cards métricos com o saldo individual de todas as contas ativas e o saldo total patrimonial consolidado.
- **FR-004**: A interface DEVE conter formulário para cadastrar novas contas, novas categorias e registrar novas transações (à vista e parceladas).
- **FR-005**: A interface DEVE renderizar barras de progresso de consumo de orçamento por categoria para o mês selecionado.
- **FR-006**: A interface DEVE incluir filtros de extrato por conta, período (data inicial e final) e opção de incluir transações pendentes/agendadas.
- **FR-007**: Todo o código e identificadores internos da interface DEVEM seguir o padrão de nomenclatura em inglês (EN-US), enquanto os textos, rótulos e mensagens da UI devem estar em português do Brasil (PT-BR).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O aplicativo web inicializa em menos de 3 segundos via comando `uv run streamlit run src/contas/ui/app.py`.
- **SC-002**: Lançamentos realizados pela interface web refletem no banco de dados com integridade matemática exata em `Decimal`.
- **SC-003**: Layout responsivo adaptado para visualização em telas de computadores e smartphones.

---

## Assumptions

- Streamlit será adicionado como dependência do projeto em `pyproject.toml`.
- O aplicativo Web roda conectado à mesma base de dados PostgreSQL gerenciada pelo `podman-compose`.

