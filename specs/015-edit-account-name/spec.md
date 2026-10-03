# Feature 015: Edição de Nome e Metadados da Conta

## Contexto e Motivação
Atualmente, o sistema permite criar e listar contas financeiras, além de desativá-las ou excluí-las. No entanto, não há suporte para renomear uma conta existente (ex: mudar "Cartão" para "Cartão Magalu", ou atualizar o nome de uma instituição financeira). Quando o usuário digita um nome incorreto ou deseja reorganizar suas contas, ele precisa recriar a conta ou mantê-la com o nome desatualizado.

Esta especificação define a funcionalidade de edição do nome de contas tanto via MCP Tool / Camada de Aplicação quanto via interface web Streamlit e chat assistente.

---

## Requisitos Funcionais

- **RF-001 (Schema de Atualização de Conta)**:
  - Criar o schema `UpdateAccountInput` aceitando:
    - `account_id: UUID` (obrigatório, identificador da conta a atualizar).
    - `name: str | None` (opcional, novo nome da conta com validação de tamanho mínimo de 1 caractere).
    - `is_active: bool | None` (opcional, status de ativação da conta).
  - Configurar `model_config = ConfigDict(extra="forbid")`.

- **RF-002 (Port e Repositório)**:
  - Estender a interface `IAccountRepository` com o método `update(account: Account) -> Account`.
  - Implementar o método na classe `SQLAlchemyAccountRepository` para persistir as alterações na tabela `account`.

- **RF-003 (Caso de Uso de Atualização)**:
  - Criar o use case `UpdateAccountUseCase(IAccountRepository)` com validação:
    - Retornar erro de domínio caso a conta não exista (`AccountNotFoundError`).
    - Validar duplicidade caso o novo nome já pertença a outra conta ativa do usuário.

- **RF-004 (MCP Tool)**:
  - Registrar a ferramenta `update_account` no servidor FastMCP com payload `UpdateAccountInput`.
  - Retornar os dados atualizados da conta em formato estruturado.

- **RF-005 (Camada de UI - Streamlit)**:
  - Em `src/contas/ui/services.py`, adicionar o método `update_account(account_id: UUID, name: str, is_active: bool | None) -> dict`.
  - Na tela de Contas (`app.py`), adicionar modal ou formulário inline de edição permitindo alterar o nome da conta e salvar com feedback visual imediato.

- **RF-006 (Integração com Assistente de Chat)**:
  - Adicionar suporte à tool `update_account` no assistente financeiro (`financial_chat.py`), tratando-a como ação de escrita com geração de `PendingAction` para confirmação do usuário.

---

## Requisitos Não Funcionais

- **RNF-001 (Consistência com Clean Architecture)**: Seguir rigorosamente o fluxo Domain -> Application -> Adapters -> Infrastructure.
- **RNF-002 (Cobertura de Testes)**: Criar testes unitários para o Use Case e testes de integração cobrindo a MCP Tool `update_account`.
- **RNF-003 (Qualidade de Código)**: 100% aderente às diretrizes de formatação e lint do `ruff`.
