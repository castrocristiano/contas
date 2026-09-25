# Feature Specification: Exclusão em Lote de Contas em Configurações (009-bulk-delete-accounts)

**Feature Branch**: `feature/009-bulk-delete-accounts`

**Created**: 2026-09-25

**Status**: Implemented ✅

**Input**: Adicionar funcionalidade na aba de Configurações para selecionar e excluir/desativar múltiplas contas financeiras de uma só vez, com suporte opcional a exclusão em cascata (force_cascade).

---

## Cenários de Usuário & Testes

### User Story 1 — Seleção Múltipla e Exclusão em Lote de Contas (Priority: P1) 🎯 MVP
Como gestor financeiro,  
Quero selecionar várias contas financeiras na tela de Configurações usando uma tabela interativa ou multiselect e confirmar a exclusão com um único clique,  
Para limpar contas duplicadas, de teste ou desnecessárias rapidamente sem precisar excluir uma por uma.

**Acceptance Scenarios**:
1. **Given** 3 contas selecionadas na lista de exclusão em lote, **When** o usuário clica em "Excluir Contas Selecionadas", **Then** cada conta é processada via `UIService.delete_account`, apresentando um relatório consolidado de sucesso e erros (se houver).
2. **Given** a opção "Exclusão em cascata (Cascade)" desmarcada, **When** contas com movimentações são excluídas, **Then** elas são desativadas (soft-delete), preservando integridade referencial.
3. **Given** a opção "Exclusão em cascata (Cascade)" marcada, **When** confirmada, **Then** as transações vinculadas e as contas são removidas permanentemente do banco.
4. **Given** nenhuma conta selecionada, **When** o botão for clicado, **Then** o sistema exibe alerta instrutivo sem disparar requisições.

---

## Requisitos

### Requisitos Funcionais
- **RF-001**: A tela de Configurações DEVE disponibilizar uma tabela interativa (`st.data_editor` com seleção) ou componente `st.multiselect` para seleção de múltiplas contas a excluir.
- **RF-002**: O usuário DEVE poder optar por exclusão padrão (soft-delete se houver transações) ou forçada em cascata (`force_cascade=True`).
- **RF-003**: Deve haver diálogo/botão de confirmação antes de disparar a exclusão das contas selecionadas.
- **RF-004**: Ao concluir o lote, um feedback consolidado DEVE ser exibido indicando quantas contas foram excluídas/desativadas com sucesso.

---

## Critérios de Sucesso
- **CS-001**: O usuário consegue apagar ou desativar N contas simultaneamente com feedback individual/consolidado.
- **CS-002**: Testes automatizados cobrindo a funcionalidade passam 100%.
