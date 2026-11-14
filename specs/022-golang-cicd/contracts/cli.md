# CLI Contract: Interface de Comandos e Parâmetros (022-golang-cicd)

**Feature**: `022-golang-cicd`  
**Data**: 2026-11-14  
**Status**: Concluído

Este documento define o contrato de interface da linha de comando da ferramenta `contas-ci`.

---

## 1. Visão Geral da CLI

```text
contas-ci [command] [flags]
```

### Comandos Principais

| Comando | Descrição | Equivalente Anterior |
|:---|:---|:---|
| `contas-ci check` | Executa o pipeline de validação básica (lint, format-check, migrations e pytest com coverage). | Steps do job `build-and-test` |
| `contas-ci lint` | Executa a checagem estática com Ruff (`uv run ruff check .`). | Step `Run Ruff Linter` |
| `contas-ci format-check` | Executa checagem de formatação e gera artefatos SonarFormatter. | Step `Run Ruff Formatter Check` |
| `contas-ci test` | Executa migrações do banco e testes unitários com cobertura XML. | Steps `alembic upgrade` + `pytest` |
| `contas-ci sonar` | Executa ciclo completo do SonarQube (health check, token, scanner e quality gate). | Substitui `sonar_check.sh` |
| `contas-ci all` | Executa `check` seguido de `sonar`. | Pipeline completo local |

---

## 2. Flags Globais e Específicas

### Flags Globais

- `--verbose`, `-v`: Habilita logs detalhados de cada comando executado e saída bruta de rede.
- `--dir`: Diretório raiz do projeto (padrão: diretório corrente ou detecção automática via `.git`).

### Flags do Comando `sonar`

- `--sonar-url`: URL do servidor SonarQube (padrão: `$SONAR_HOST_URL` ou `http://192.168.1.20:9000`).
- `--token`: Token de autenticação do SonarQube (padrão: resolução automática pela prioridade).
- `--container-engine`: Engine de containers a utilizar (`podman` ou `docker`, padrão: detecção automática).
- `--skip-scanner`: Valida apenas conectividade e Quality Gate existente sem invocar o container scanner.
- `--timeout`: Duração máxima de espera pelo processamento do Quality Gate (padrão: `5m`).

### Flags do Comando `test`

- `--skip-migrations`: Executa os testes sem disparar `alembic upgrade head`.
- `--coverage-file`: Caminho de saída do relatório de cobertura (padrão: `coverage.xml`).

---

## 3. Variáveis de Ambiente Suportadas

| Variável | Descrição | Padrão |
|:---|:---|:---|
| `SONAR_HOST_URL` | URL do servidor SonarQube | `http://192.168.1.20:9000` |
| `SONAR_TOKEN` | Token prioritário para autenticação | Arquivo `.env` ou `.sonar_remote_token` |
| `DATABASE_URL` | Conexão para migrações e testes de integração | `postgresql+psycopg://contas:contas@localhost:5432/contas` |
| `CONTAINER_ENGINE` | Override forçado da engine de container | Detecção automática (`podman` -> `docker`) |

---

## 4. Códigos de Retorno (Exit Codes)

| Código | Significado | Ação Esperada |
|:---|:---|:---|
| `0` | Sucesso total em todas as etapas executadas. | Pipeline aprovado. |
| `1` | Falha em etapa de validação (lint, testes, formatação ou Quality Gate REPROVADO). | Aborta o pipeline e exibe relatório de falhas. |
| `2` | Erro de configuração ou pré-requisito ausente (ex: SonarQube DOWN, token inválido). | Exibe instruções de correção de infraestrutura. |
