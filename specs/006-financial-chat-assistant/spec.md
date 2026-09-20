# Feature Specification: Assistente Financeiro por Chat na Tela Principal (006-financial-chat-assistant)

**Feature Branch**: `feature/006-financial-chat`

**Created**: 2026-09-20

**Status**: Draft

**Input**: Sessão de chat com IA na tela principal do app Streamlit para consultar e interagir com as finanças do usuário em linguagem natural.

---

## Cenários de Usuário & Testes

### User Story 1 — Consulta Financeira via Chat em Linguagem Natural (Priority: P1) 🎯 MVP

Como usuário do sistema Contas,  
Quero fazer perguntas em linguagem natural ao assistente financeiro (ex: "Qual meu saldo total?", "Quanto gastei em setembro com alimentação?"),  
Para que eu obtenha respostas claras e precisas sem precisar navegar por múltiplas telas.

**Why this priority**: É o valor central da feature — acesso rápido e contextualizado a dados financeiros.

**Independent Test**: Perguntar "qual meu saldo total?" e verificar que o assistente chama `list_accounts` e responde com os saldos corretos formatados em R$.

**Acceptance Scenarios**:
1. **Given** contas cadastradas no sistema, **When** o usuário digita "qual meu saldo total?", **Then** o assistente lista as contas com saldo e o total consolidado em formato R$.
2. **Given** transações registradas no mês corrente, **When** o usuário pergunta "quanto gastei em setembro?", **Then** o assistente chama `get_financial_summary` e responde com total de despesas no período.
3. **Given** um período especificado, **When** o usuário pede "mostre minhas últimas 10 transações", **Then** o assistente chama `get_statement` e lista as transações no chat.

---

### User Story 2 — Registro de Transação via Chat com Confirmação (Priority: P2)

Como usuário,  
Quero ditar um lançamento ao assistente (ex: "Lance R$ 80 de supermercado hoje na conta Nubank"),  
Para que o sistema proponha a transação com um resumo legível e eu confirme com um clique antes de persistir.

**Why this priority**: Reduz o atrito de lançamento manual mantendo controle e segurança do usuário.

**Independent Test**: Pedir ao assistente "lance R$ 50 de gasolina" e verificar que aparece um bloco de confirmação com os dados resumidos; ao confirmar, a transação é persistida.

**Acceptance Scenarios**:
1. **Given** o usuário digita "registre R$ 120 de mercado hoje", **When** o assistente interpreta a instrução, **Then** exibe um bloco de confirmação com tipo, valor, descrição, conta e categoria antes de efetivar.
2. **Given** o bloco de confirmação exibido, **When** o usuário clica em "Confirmar", **Then** `record_transaction` é chamado e a transação aparece no extrato.
3. **Given** o bloco de confirmação exibido, **When** o usuário clica em "Cancelar", **Then** nenhuma transação é persistida e o chat continua normalmente.

---

### User Story 3 — Consulta de Orçamentos e Alertas (Priority: P3)

Como usuário,  
Quero perguntar ao assistente sobre o estado dos meus orçamentos (ex: "Estou dentro do orçamento de alimentação?"),  
Para monitorar metas de gastos sem sair da tela principal.

**Why this priority**: Agrega valor analítico ao chat sem implementação adicional no backend.

**Independent Test**: Perguntar "como estão meus orçamentos de setembro?" e verificar que o assistente chama `get_budget_status` e lista categorias com % consumido.

**Acceptance Scenarios**:
1. **Given** orçamentos cadastrados, **When** o usuário pergunta "como estão meus orçamentos?", **Then** o assistente lista categorias, % consumido e saldo restante.
2. **Given** um orçamento estourado, **When** consultado, **Then** o assistente destaca o excedente com linguagem clara (ex: "Você ultrapassou o limite de Alimentação em R$ 45,00").

---

## Requisitos

### Requisitos Funcionais

- **RF-001**: O chat DEVE usar OpenAI function calling (não Structured Outputs) com ferramentas mapeadas para `list_accounts`, `list_categories`, `get_financial_summary`, `get_statement`, `get_budget_status` e `record_transaction`.
- **RF-002**: Ações de escrita (`record_transaction`) DEVEM passar por confirmação explícita do usuário antes de serem executadas — o assistente não pode persistir dados sem interação.
- **RF-003**: O histórico de conversa DEVE ser mantido no `st.session_state` e limpo ao resetar a sessão.
- **RF-004**: Respostas do assistente DEVEM ser sempre em Português do Brasil.
- **RF-005**: O módulo de chat DEVE aceitar um `client: OpenAI | None` injetável para facilitar testes com mocks.
- **RF-006**: A chave da API DEVE respeitar o mesmo fallback da feature 005: `OPENAPI_KEY` → `OPENAI_API_KEY` → `OPENAIAPI_KEY` → `~/.openai_key`.

### Requisitos Não Funcionais

- **RNF-001**: O chat DEVE funcionar dentro da interface Streamlit existente como nova opção no menu lateral.
- **RNF-002**: Testes unitários DEVEM usar estritamente mocks — sem chamadas reais à OpenAI.
- **RNF-003**: O código DEVE seguir o padrão de linting (`ruff`) e formatação do projeto.

## Casos de Borda

- **Sem contas cadastradas**: O assistente deve orientar o usuário a criar uma conta primeiro.
- **API key ausente**: Exibir mensagem amigável em PT-BR pedindo para configurar a chave.
- **Pergunta ambígua de conta**: Se o usuário mencionar uma conta que não existe, o assistente pergunta qual das contas disponíveis usar.
- **Loop de tool calls**: O loop agentic é limitado a 6 iterações para evitar consumo excessivo de tokens.

## Critérios de Sucesso

- **CS-001**: O assistente responde corretamente a perguntas de saldo e extrato usando dados reais do banco.
- **CS-002**: Toda ação de escrita passa pela tela de confirmação — zero persistências silenciosas.
- **CS-003**: 100% dos testes unitários passam usando mocks.
- **CS-004**: Nenhum aviso de depreciação ou erro de linting novo introduzido.
