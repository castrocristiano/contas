# Feature Specification: Cobertura Completa de Ferramentas MCP no Chat Financeiro (007-chat-full-mcp-tools)

**Feature Branch**: `feature/007-chat-full-mcp-tools`

**Created**: 2026-09-20

**Status**: Implemented ✅

**Input**: Adicionar todas as ferramentas MCP restantes ao assistente financeiro no chat, garantindo confirmação explícita para quaisquer operações de alteração ou exclusão de dados.

---

## Mapeamento de Ferramentas MCP

| Ferramenta MCP | Tipo de Operação | Requer Confirmação? | Status no Chat |
|---|---|---|---|
| `list_accounts` | Leitura | Não | Suportado |
| `list_categories` | Leitura | Não | Suportado |
| `get_financial_summary` | Leitura | Não | Suportado |
| `get_statement` | Leitura | Não | Suportado |
| `get_budget_status` | Leitura | Não | Suportado |
| `get_installment_plan` | Leitura | Não | Suportado |
| `record_transaction` | Escrita | Sim | Suportado |
| `create_account` | Escrita | Sim | Suportado |
| `create_category` | Escrita | Sim | Suportado |
| `set_budget` | Escrita/Alteração | Sim | Suportado |
| `delete_transaction` | Exclusão | Sim | Suportado |
| `delete_account` | Exclusão | Sim | Suportado |

---

## Cenários de Usuário & Testes

### User Story 1 — Consulta de Detalhes de Parcelamento (`get_installment_plan`) (Priority: P1)
Como usuário,  
Quero perguntar no chat sobre o plano de parcelamento de uma compra (ex: "Mostre o plano de parcelas da compra do notebook"),  
Para verificar quantas parcelas já foram pagas e quantas ainda faltam.

**Acceptance Scenarios**:
1. **Given** transações com parcelamento cadastrado, **When** o usuário solicita detalhes das parcelas, **Then** o assistente obtém o plano via `get_installment_plan` e responde com valor total, parcelas pagas, parcelas pendentes e datas de vencimento.

---

### User Story 2 — Criação de Categorias e Orçamentos com Confirmação (Priority: P1)
Como usuário,  
Quero pedir para o assistente criar uma categoria (ex: "Crie a categoria Farmácia para despesas") ou definir uma meta de orçamento (ex: "Defina o orçamento de Alimentação em R$ 800 para este mês"),  
Para gerenciar meus limites e categorias sem sair do chat, com segurança via confirmação prévia.

**Acceptance Scenarios**:
1. **Given** comando "Crie a categoria Lazer de despesa", **When** processado, **Then** o assistente apresenta o resumo da nova categoria com botões de Confirmação antes de persistir.
2. **Given** comando "Defina o orçamento de Alimentação em R$ 600 em setembro/2026", **When** processado, **Then** o assistente apresenta o resumo da alteração de orçamento e aguarda confirmação.

---

### User Story 3 — Exclusão de Transações e Contas com Confirmação e Estorno (Priority: P1)
Como usuário,  
Quero pedir para excluir uma transação ou remover uma conta pelo chat (ex: "Exclua a despesa de R$ 35 de farmácia de ontem"),  
Para corrigir erros de lançamento rapidamente com segurança total.

**Acceptance Scenarios**:
1. **Given** uma transação existente encontrada no extrato, **When** o usuário solicita exclusão, **Then** o assistente localiza a transação, monta a `PendingAction` destacando que o saldo será estornado, e exige confirmação.
2. **Given** uma transação parcelada, **When** o usuário solicita exclusão, **Then** o assistente oferece/configura a opção de remover apenas a parcela ou todas as parcelas (`delete_all_installments`).
3. **Given** pedido de exclusão de conta, **When** processado, **Then** o assistente monta confirmação detalhada para `delete_account` com aviso de desativação ou exclusão.

---

## Requisitos

### Requisitos Funcionais
- **RF-001**: O assistente financeiro DEVE expor todas as ferramentas MCP disponíveis no sistema: `create_category`, `set_budget`, `get_installment_plan`, `delete_transaction` e `delete_account`.
- **RF-002**: Toda operação que crie, modifique ou exclua registros (`_WRITE_TOOLS`) DEVE retornar `PendingAction` e exigir clique em "Confirmar" na interface Streamlit antes de executar.
- **RF-003**: Ações de exclusão (`delete_transaction`, `delete_account`) DEVEM apresentar alertas visuais claros sobre estorno de saldo e impactos.
- **RF-004**: O assistente deve conseguir buscar a transação pelo extrato se o usuário não passar o UUID diretamente (ex: buscando por valor/descrição antes de sugerir a exclusão).

---

## Critérios de Sucesso
- **CS-001**: 100% das ferramentas MCP do sistema estão acessíveis através do assistente conversacional.
- **CS-002**: Nenhuma operação destrutiva ou de alteração é executada sem confirmação explícita do usuário.
- **CS-003**: Todos os testes unitários cobrem as novas ferramentas com mocks e passam 100%.
