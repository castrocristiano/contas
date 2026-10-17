---
name: formatter
description: >-
  Use this skill to format Python code with Ruff, validate code style and lint rules,
  and generate SonarQube formatter issue reports before committing, pushing, or running
  SonarQube analysis.
---

# Formatter & Lint Skill (`ruff` + SonarQube)

Esta skill padroniza a formatação automática de código, verificação de lint com **Ruff** e geração de relatórios de formatação para o **SonarQube** no projeto **Contas**.

## Quando Utilizar

- Sempre após criar ou editar arquivos Python (`src/` ou `tests/`).
- Obrigatoriamente **antes** de realizar `git commit`, `git push` ou `./sonar_check.sh`.
- Quando solicitado pelo usuário para formatar o código ou validar regras de formatação no SonarQube.

## Passo a Passo

### 1. Aplicar Formatação e Correções Automáticas de Lint

Execute o Ruff utilizando o binário do ambiente virtual do projeto (`.venv/bin/ruff` ou `uv run ruff`):

```bash
.venv/bin/ruff check --fix .
.venv/bin/ruff format .
```

### 2. Verificar Conformidade Estrita (Modo CI)

Confirme que nenhum arquivo possui erros de lint ou divergências de formatação:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

### 3. Gerar Relatórios de Regra de Formatter para o SonarQube

Para que o SonarQube contabilize violações de formatação (`ruff-formatter:unformatted-file`) e de lint (`sonar.python.ruff.reportPaths`) diretamente no Dashboard e no Quality Gate, execute o script auxiliar da skill:

- Script: [sonar_formatter_check.py](./scripts/sonar_formatter_check.py)

```bash
python3 .agents/skills/formatter/scripts/sonar_formatter_check.py
```

Para auto-formatar antes de gerar o relatório:

```bash
python3 .agents/skills/formatter/scripts/sonar_formatter_check.py --fix
```

### 4. Prioridade do `SONAR_TOKEN` na Integração SonarQube (`./sonar_check.sh`)

Ao executar `./sonar_check.sh` ou comunicar com a API do SonarQube (`dc1` ou CI), a autenticação **sempre prioriza o token do Sonar** (`-u "${SONAR_TOKEN}:"`) na seguinte ordem de resolução:
1. Variável de ambiente `SONAR_TOKEN` exportada na sessão / CI Secrets.
2. Variável `SONAR_TOKEN` definida no arquivo `.env`.
3. Arquivos locais `.sonar_token` ou `.sonar_remote_token` (`chmod 600`).

## Critérios de Conclusão

- [ ] `.venv/bin/ruff check .` retorna `All checks passed!` (exit code `0`).
- [ ] `.venv/bin/ruff format --check .` retorna `N files already formatted` (exit code `0`).
- [ ] Relatórios `sonar-formatter-issues.json` e `ruff-report.json` gerados sem issues pendentes ao rodar `./sonar_check.sh` autenticado via `SONAR_TOKEN`.

