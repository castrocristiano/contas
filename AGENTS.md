# Diretrizes do Projeto Contas (AGENTS.md)

## Idioma e Convenções de Linguagem

### 1. Documentação e Interação (PT-BR)
- **Comunicação e Interação**: Todas as respostas ao usuário, perguntas, explicações e relatórios DEVEM ser fornecidos em **Português do Brasil (PT-BR)**.
- **Artefatos do Spec Kit**: Todos os arquivos de especificação (`spec.md`), planejamento arquitetural (`plan.md`), listas de tarefas (`tasks.md`), checklists e `README.md` DEVEM ser redigidos em **Português do Brasil (PT-BR)**.
- **Mensagens de Git**: As mensagens de commit seguem Conventional Commits com descrição preferencialmente em português (ex: `feat(infra): adicionar configuracao do podman-compose`).

### 2. Código-Fonte (EN-US)
- **Código-Fonte em Inglês**: Todo o código-fonte DEVE ser escrito em **Inglês (EN-US)**.
- **Identificadores**: Nomes de classes, funções, métodos, variáveis, módulos, schemas Pydantic, tabelas e colunas do PostgreSQL DEVEM ser em inglês (ex: `Account`, `Transaction`, `Category`, `balance`, `amount`, `transaction_type`, `create_account`, `record_transaction`).
- **Docstrings e Comentários de Código**: Devem ser redigidos em inglês no código-fonte.
- **Testes**: Arquivos e funções de teste devem seguir nomenclatura em inglês (ex: `test_create_transaction_success()`, `test_invalid_amount_raises_error()`).
