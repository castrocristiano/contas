# Feature Specification: Registro e Gestão de Compras Parceladas via Chat (008-chat-installment-purchases)

**Feature Branch**: `feature/008-chat-installment-purchases`

**Created**: 2026-09-25

**Status**: Implemented ✅

**Input**: No chat financeiro, compras parceladas estavam sendo cadastradas como transações únicas (à vista) porque a ferramenta `record_transaction` no chat não expunha parâmetros de parcelamento (`total_installments` e `total_amount`), e o executor não os repassava para o backend.

---

## Cenários de Usuário & Testes

### User Story 1 — Registro de Compra Parcelada via Chat (Priority: P1) 🎯 MVP
Como usuário do sistema Contas,  
Quero solicitar ao assistente o cadastro de uma compra parcelada (ex: "Cadastre uma compra na PicPay de QUINJALMO em 10 vezes de R$ 216,81" ou "Compra de R$ 1.200 em 6x"),  
Para que todas as parcelas sejam geradas mensalmente com suas datas e status correspondentes, vinculadas a um `installment_id`.

**Acceptance Scenarios**:
1. **Given** o usuário informa "lance R$ 2.168,10 em 10x na conta PicPay", **When** o assistente processa a solicitação, **Then** a ferramenta `record_transaction` é proposta com `total_installments=10`, `total_amount="2168.10"` e `amount="216.81"`.
2. **Given** o usuário informa "lance 10 vezes de R$ 216,81", **When** o assistente calcula o total ou recebe os parâmetros, **Then** a confirmação exibe claramente: "10x de R$ 216,81 (Total: R$ 2.168,10)".
3. **Given** a confirmação aprovada pelo usuário, **When** `execute_pending_action` roda, **Then** todas as 10 parcelas são geradas no banco via `UIService.record_transaction` com metadados de parcelamento preservados.

---

### User Story 2 — Resumo de Confirmação Claro para Parcelamentos (Priority: P2)
Como usuário,  
Quero ver no bloco de confirmação da UI que se trata de uma compra parcelada e o número de parcelas,  
Para ter certeza de que não será lançada como compra à vista antes de clicar em Confirmar.

**Acceptance Scenarios**:
1. **Given** uma transação com `total_installments > 1`, **When** o resumo é gerado por `_build_action_summary`, **Then** exibe "Parcelamento em 10x de R$ 216,81 | Total: R$ 2.168,10".

---

## Requisitos

### Requisitos Funcionais
- **RF-001**: O schema de `record_transaction` em `_TOOLS` DEVE expor `total_installments` (inteiro opcional >= 1) e `total_amount` (string decimal opcional).
- **RF-002**: `execute_pending_action` DEVE repassar `total_installments` e `total_amount` para `UIService.record_transaction`.
- **RF-003**: `_build_action_summary` DEVE formatar compras parceladas indicando a quantidade de parcelas, o valor de cada parcela e o valor total.
- **RF-004**: O `SYSTEM_PROMPT` DEVE instruir a IA a identificar compras parceladas em linguagem natural (ex: "em 10x", "parcelado em 3 vezes") e preencher `total_installments` e `total_amount` / `amount`.

---

## Critérios de Sucesso
- **CS-001**: Ao pedir para cadastrar compras parceladas, todas as parcelas são persistidas com `installment_id`, `installment_number` e `total_installments`.
- **CS-002**: 100% dos testes unitários passam usando mocks.
