# Feature Specification: Gestão de Categorias e Orçamentos (002-categories-and-budgets)

**Feature Branch**: `feature/002-categories-and-budgets`

**Created**: 2026-09-19

**Status**: Draft

**Input**: User description: "Gestão completa de categorias (criação, listagem, inativação) e definição de orçamentos (budgets) com acompanhamento de metas de gastos por período e alertas de limites atingidos."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerenciamento de Categorias de Receitas e Despesas (Priority: P1) 🎯 MVP

Como usuário do sistema de gestão financeira,
Quero poder criar e listar categorias organizadas por tipo (receita ou despesa),
Para que eu possa classificar minhas transações financeiras com clareza e consistência.

**Why this priority**: Categorias são pré-requisito funcional direto tanto para a correta classificação das despesas quanto para a definição e monitoramento de orçamentos por área de gasto.

**Independent Test**: Pode ser testado criando uma categoria (ex: "Alimentação", tipo "despesa") e listando as categorias ativas, verificando a persistência e categorização correta.

**Acceptance Scenarios**:
1. **Given** que o usuário deseja cadastrar uma categoria de despesa, **When** fornece nome único e tipo `expense`, **Then** a categoria é criada com sucesso em estado ativo.
2. **Given** categorias cadastradas no sistema, **When** o usuário solicita a listagem de categorias, **Then** o sistema retorna as categorias ativas agrupadas ou filtradas por tipo (`income` ou `expense`).
3. **Given** uma categoria já existente com o mesmo nome, **When** o usuário tenta cadastrá-la novamente com o mesmo nome, **Then** o sistema recusa a duplicidade retornando erro de validação.

---

### User Story 2 - Definição de Tetos de Gastos / Orçamentos Mensais (Priority: P2)

Como usuário que deseja manter controle financeiro preventivo,
Quero definir um orçamento mensal de gastos para categorias específicas (ex: "Lazer: R$ 400,00" para setembro/2026),
Para que o sistema estabeleça um limite claro de consumo para aquele período.

**Why this priority**: O orçamento estabelece a meta e o teto planejado para o mês, transformando o sistema de um simples livro-caixa em uma ferramenta de planejamento financeiro.

**Independent Test**: Pode ser testado cadastrando um orçamento para uma categoria em determinado mês/ano e consultando os orçamentos ativos do período.

**Acceptance Scenarios**:
1. **Given** uma categoria de despesa existente e ativa, **When** o usuário define um valor limite mensal e o período de referência (mês e ano), **Then** o orçamento é registrado com sucesso.
2. **Given** um orçamento já existente para a mesma categoria e mesmo mês/ano, **When** o usuário submete um novo valor de orçamento, **Then** o sistema atualiza o valor do teto existente ou notifica a existência de limite prévio.
3. **Given** uma tentativa de criar orçamento com valor menor ou igual a zero, **When** a solicitação é processada, **Then** o sistema rejeita a operação com erro estruturado.

---

### User Story 3 - Acompanhamento de Execução Orçamentária e Status de Consumo (Priority: P3)

Como usuário acompanhando meus gastos ao longo do mês,
Quero consultar o relatório de execução do orçamento comparando o limite previsto com o total já consumido nas transações,
Para que eu saiba quanto já gastei, quanto ainda tenho disponível e se ultrapassei o teto planejado.

**Why this priority**: Fornece visibilidade em tempo real sobre a saúde dos limites estipulados e alerta desvios orçamentários.

**Independent Test**: Pode ser testado registrando transações em uma categoria com orçamento e consultando o status do orçamento para verificar se o valor gasto, saldo restante e percentual consumido são calculados com precisão.

**Acceptance Scenarios**:
1. **Given** um orçamento de R$ 500,00 e despesas totalizando R$ 350,00 no mês, **When** o usuário consulta o status do orçamento, **Then** o sistema exibe: previsto: R$ 500,00, realizado: R$ 350,00, saldo restante: R$ 150,00, percentual: 70%, status: dentro do limite.
2. **Given** um orçamento de R$ 200,00 e despesas totalizando R$ 250,00 no mês, **When** o usuário consulta o status do orçamento, **Then** o sistema indica status de orçamento estourado/excedido com valor excedente de R$ 50,00 (125%).

---

### Edge Cases

- **Inativação de Categoria em Uso**: Quando uma categoria vinculada a transações passadas é desativada, o sistema aplica soft delete (`is_active = False`) para manter histórico imutável.
- **Transação em Categoria Inativa**: Tentativas de registrar novas transações em categorias inativas são bloqueadas.
- **Orçamento sem Gastos Realizados**: Se o período corrente ainda não tiver transações registradas para a categoria orçada, o valor realizado deve ser `0.00`, com 100% de saldo restante.
- **Múltiplas Moedas no Orçamento**: Orçamentos devem respeitar a moeda da conta ou operar na moeda padrão do sistema (`BRL`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE permitir a criação de categorias com nome, tipo (`income` ou `expense`) e estado ativo.
- **FR-002**: O sistema DEVE garantir a unicidade de nome para cada categoria cadastrada.
- **FR-003**: O sistema DEVE disponibilizar listagem de categorias com opção de filtragem por tipo e por status de atividade.
- **FR-004**: O sistema DEVE permitir a inativação lógica (*soft delete*) de categorias sem excluir transações históricas associadas.
- **FR-005**: O sistema DEVE permitir definir orçamentos mensais com valor teto exato (`Decimal`), categoria associada, mês e ano de vigência.
- **FR-006**: O sistema DEVE calcular a execução orçamentária somando todas as despesas liquidadas da respectiva categoria dentro do mês/ano de vigência do orçamento.
- **FR-007**: O sistema DEVE retornar métricas consolidadas de consumo: total orçado, total gasto, saldo restante e percentual de consumo.
- **FR-008**: Todas as operações financeiras e limites orçamentários DEVEM utilizar exclusivamente representação decimal exata (`Decimal` / centavos), sem uso de ponto flutuante binário.

### Key Entities *(include if feature involves data)*

- **Category**: Representa um agrupador de receitas ou despesas. Atributos: `id`, `name`, `category_type` (Enum: `income`, `expense`), `is_active`, `created_at`.
- **Budget**: Representa o planejamento/teto de gastos de uma categoria para um período temporal específico. Atributos: `id`, `category_id` (FK para `Category`), `amount` (Decimal exato), `month` (1 a 12), `year` (ex: 2026), `created_at`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuários conseguem cadastrar novas categorias e consultar a lista existente via ferramentas MCP em menos de 1 segundo.
- **SC-002**: 100% dos cálculos de execução orçamentária (total orçado vs. total gasto vs. saldo restante) utilizam precisão decimal exata sem divergências de arredondamento.
- **SC-003**: O sistema impede com 100% de eficácia a exclusão física de categorias vinculadas a registros contábeis históricos.
- **SC-004**: A visualização de status orçamentário reflete imediatamente quaisquer novas transações inseridas no mesmo período.

---

## Assumptions

- Orçamentos operam por padrão na granularidade mensal (mês/ano), alinhada ao ciclo padrão de fechamento doméstico.
- O controle orçamentário se aplica primariamente a despesas (`expense`), visto que receitas representam entradas e não tetos limitadores de gasto.
- A autenticação e segurança seguem o mesmo modelo do servidor MCP configurado na feature `001-core-infra-mcp`.
- O banco de dados PostgreSQL 16 provisionado via Podman continuará sendo a fonte primária de persistência.
