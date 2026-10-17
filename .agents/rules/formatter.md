---
trigger: always_on
description: "Garante formatação com Ruff (ruff format e ruff check) antes de qualquer commit, push ou análise SonarQube"
---

# Regra: Formatação Obrigatória de Código (Ruff Formatter & SonarQube)

1. **Formatação Automática Pós-Edição**: Sempre que criar ou modificar arquivos `.py` em `src/` ou `tests/`, o agente DEVE executar `.venv/bin/ruff check --fix .` e `.venv/bin/ruff format .`.
2. **Gate Pré-Commit / Pré-Push**: Antes de executar `git commit` ou `git push`, o agente DEVE validar que `.venv/bin/ruff check .` e `.venv/bin/ruff format --check .` passam com código de saída `0` (ou acionar a skill `formatter`).
3. **Integração com SonarQube e Prioridade do `SONAR_TOKEN`**:
   - O script `./sonar_check.sh` avalia a regra de formatação exportando divergências via `sonar-formatter-issues.json` (`ruff-formatter:unformatted-file`) e `ruff-report.json`.
   - Toda comunicação com o SonarQube DEVE priorizar o `SONAR_TOKEN` (variável de ambiente `SONAR_TOKEN` -> `.env` -> `.sonar_token` / `.sonar_remote_token`), sem credenciais de senha hardcoded nos scripts.
