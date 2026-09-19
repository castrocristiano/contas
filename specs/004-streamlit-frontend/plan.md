# Plano de Implementação: Interface Web com Streamlit (004-streamlit-frontend)

**Feature Branch**: `feature/004-streamlit-frontend` | **Data**: 2026-09-19
**Spec**: [spec.md](./spec.md)

---

## 1. Visão Geral da Arquitetura

A interface web será construída em **Streamlit**, mantendo a premissa de simplicidade e **100% Python** sem sobrecarga de build JavaScript:
- Adição da dependência `streamlit>=1.35.0` no `pyproject.toml`.
- Módulo `src/contas/ui/` estruturado com:
  - `app.py`: ponto de entrada do Streamlit com navegação lateral (Dashboard, Extrato, Novo Lançamento, Orçamentos).
  - `services.py`: adaptadores/funções de serviço para consultar e gravar dados usando as mesmas regras de negócio e validações Pydantic das ferramentas MCP.
  - `components.py`: cards de saldos, barras de progresso orçamentário e tabelas customizadas com formatação monetária (R$).
- Execução direta com comando `uv run streamlit run src/contas/ui/app.py` ou script CLI `contas-ui`.

---

## 2. Fases de Implementação

### Fase 1: Dependências & Estrutura Base
1. Adicionar `streamlit` ao `pyproject.toml` e sincronizar com `uv sync`.
2. Criar diretório `src/contas/ui/` e arquivos base.

### Fase 2: Camada de Serviços da UI
1. Implementar `src/contas/ui/services.py` para execução de queries e operações reutilizando a sessão de banco assíncrona/síncrona de forma segura para o ciclo de renderização do Streamlit.

### Fase 3: Dashboard & Extrato (US1 - MVP)
1. Implementar visão geral com métricas: Total Patrimonial, saldos por conta.
2. Tabela de extrato com filtros por conta e período, badges e suporte a pendências/parcelas.

### Fase 4: Formulários de Lançamento (US2)
1. Formulário para Nova Transação (Receita, Despesa e Transferência).
2. Suporte integrado a compras parceladas (número de parcelas e geração automática).
3. Formulários rápidos para Nova Conta e Nova Categoria.

### Fase 5: Acompanhamento de Orçamentos (US3)
1. Página de Orçamentos: definição de metas mensais e barras de progresso com alerta de limite estourado.
2. Consulta de Planos de Compras Parceladas ativas.

### Fase 6: Polish, Testes e Documentação
1. Testes unitários para camada de serviços da UI em `tests/unit/test_ui_services.py`.
2. Atualização de `README.md` com instruções de inicialização do frontend.
3. Lint e testes (`ruff`, `pytest`).

