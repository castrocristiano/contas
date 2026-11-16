# Implementation Plan: Remoção do o3-mini e Carregamento Dinâmico de Modelos OpenAI (024-dynamic-llm-models)

**Branch**: `feature/024-dynamic-llm-models` | **Date**: 2026-11-15 | **Spec**: [specs/024-dynamic-llm-models/spec.md](spec.md)

**Input**: Feature specification from `/specs/024-dynamic-llm-models/spec.md`

---

## Summary

Remover integralmente o modelo deprecado `o3-mini` de todo o sistema Contas, definindo `gpt-4o` como o novo modelo padrão estável. Implementar a descoberta e o carregamento dinâmico de modelos via API da OpenAI (`client.models.list()`) com cache inteligente e fallback resiliente (`gpt-4o`, `gpt-4o-mini`, `o1`), além de controle visual no Streamlit para atualização manual sob demanda.

---

## Technical Context

**Language/Version**: Python 3.12+ gerenciado via `uv`.

**Primary Dependencies**: `openai>=1.0`, `streamlit>=1.35.0`, `pydantic-settings>=2.0`.

**Storage**: Cache em memória (módulo Python) com expiração por TTL.

**Testing**: `pytest`, `pytest-cov`, `unittest.mock` para simulação da API de modelos da OpenAI.

**Constraints**: Não quebrar a aplicação caso a chave da OpenAI não esteja configurada ou ocorram falhas de conexão; garantir que `o3-mini` não seja mais solicitado em nenhuma requisição.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação | Status |
|:---|:---|:---:|
| **I. Simplicidade e YAGNI** | Uso da API nativa da OpenAI (`client.models.list()`) com filtro leve em memória e fallback direto. | **APROVADO** |
| **IV. Integração com IA Segura e Estruturada** | Garante que os modelos selecionados suportem Chat e Structured Outputs. | **APROVADO** |
| **VI. Idioma** | Documentação e UI em PT-BR; código e identificadores em EN-US (`openai_models.py`, `get_available_openai_models`). | **APROVADO** |

---

## Project Structure

### Documentation (this feature)

```text
specs/024-dynamic-llm-models/
├── spec.md              # Especificação de requisitos da funcionalidade
├── plan.md              # Plano mestre de implementação (este documento)
├── research.md          # Decisões arquiteturais e alternativas
├── data-model.md        # Estruturas de filtro e cache
├── quickstart.md        # Guia rápido de validação
├── contracts/
│   └── models_contracts.md # Assinaturas de métodos e UI
└── checklists/
    └── requirements.md  # Validação de qualidade
```

### Source Code Layout

```text
src/contas/
├── config.py                     # Atualiza invoice_model padrão para "gpt-4o"
├── services/
│   ├── openai_models.py          # Novo serviço de listagem dinâmica e cache de modelos
│   └── invoice_parser.py         # Remove referências residuais a o3-mini
└── ui/
    └── app.py                    # Seletor dinâmico e botão de refresh de modelos

tests/
└── unit/
    └── test_openai_models.py     # Testes unitários de descoberta, filtro e fallback
```
