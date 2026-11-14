# Implementation Plan: Migração e Unificação do CI/CD com Go Lang (022-golang-cicd)

**Branch**: `feature/022-golang-cicd` | **Date**: 2026-11-14 | **Spec**: [specs/022-golang-cicd/spec.md](spec.md)

**Input**: Feature specification from `/specs/022-golang-cicd/spec.md`

---

## Summary

Migrar e unificar as rotinas de verificação contínua, testes e validação de qualidade (atualmente compostas por 183 linhas no script Bash `sonar_check.sh` e múltiplos blocos inline em `.github/workflows/ci.yml`) para uma ferramenta CLI modular e autônoma escrita em Go (`tools/ci`), executável tanto em tempo de desenvolvimento local quanto nos runners do GitHub Actions.

A ferramenta em Go orquestrará a execução das ferramentas Python (`uv`, `ruff`, `alembic`, `pytest`), implementará um cliente HTTP nativo e resiliente para a API REST do SonarQube, automatizará o disparo do SonarScanner via Podman/Docker e monitorará o veredito final do Quality Gate.

---

## Technical Context

**Language/Version**: Go 1.22+ (para a ferramenta de CI) e Python 3.12+ (ecossistema do produto principal).

**Primary Dependencies**: 
- Go: `github.com/spf13/cobra` (CLI framework), biblioteca padrão (`net/http`, `os/exec`, `context`, `encoding/json`).
- Python / Tooling orquestrado: `uv`, `ruff`, `pytest`, `alembic`.
- Containers: `docker.io/sonarsource/sonar-scanner-cli:latest` executado via Podman ou Docker.

**Storage**: Arquivos de relatórios (`coverage.xml`, `ruff-report.json`, `sonar-formatter-issues.json`), variáveis de ambiente e arquivos locais de token (`.env`, `.sonar_remote_token`).

**Testing**: 
- Go: `testing` padrão para testes unitários dos pacotes Go (`runner`, `sonar`, `config`).
- Python: `pytest` orquestrado pelo runner.

**Target Platform**: Linux (Ubuntu local e GitHub Actions Ubuntu runner), compatível com macOS e contêineres.

**Project Type**: CLI tool & Pipeline Automation runner.

**Performance Goals**: Tempo de inicialização da ferramenta inferior a 100ms; execução de health checks e retries com backoff exponencial; paridade estrita com o ambiente de CI.

**Constraints**: Não quebrar a esteira de CI existente durante a migração; manter estrita conformidade com a prioridade de resolução do `SONAR_TOKEN`.

**Scale/Scope**: Substituição integral das 183 linhas do `sonar_check.sh` e redução de pelo menos 40% nas linhas de scripts inline de `.github/workflows/ci.yml`.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio Constitucional | Avaliação | Status |
|:---|:---|:---:|
| **I. Simplicidade e YAGNI** | A ferramenta Go foca estritamente nas necessidades atuais da esteira: lint, testes, migrações e SonarQube. Sem abstrações prematuras ou dependências pesadas de daemons externos (ex: Dagger evitado). | **APROVADO** |
| **II. Integridade e Precisão Financeira** | A ferramenta Go não altera modelos de negócio nem dados contábeis; garante que as validações de cobertura e testes que protegem a precisão monetária continuem executando rigorosamente. | **APROVADO** |
| **III. Interface MCP Declarativa e Autônoma** | O produto principal e suas tools MCP permanecem intocados; a CLI Go apenas automatiza a validação da base de código. | **APROVADO** |
| **IV. Integração com IA Segura e Estruturada** | Nenhuma chamada de IA desestruturada é adicionada; as checagens estáticas do linter continuam ativas. | **APROVADO** |
| **V. Conteinerização e Portabilidade com Podman** | Mantido o suporte prioritário a `podman` em modo rootless para o SonarScanner; tokens e variáveis continuam isolados via `.env`. | **APROVADO** |
| **VI. Idioma: Documentação em PT-BR e Código em EN-US** | Especificações, planos e documentações em Português do Brasil; todo o código-fonte em Go (`tools/ci`), nomes de pacotes, structs, métodos e testes escritos em Inglês (EN-US). | **APROVADO** |

---

## Project Structure

### Documentation (this feature)

```text
specs/022-golang-cicd/
├── spec.md              # Especificação de requisitos da funcionalidade
├── plan.md              # Plano mestre de implementação (este documento)
├── research.md          # Decisões arquiteturais e alternativas avaliadas
├── data-model.md        # Modelos de dados e transições de estado em Go
├── quickstart.md        # Guia passo a passo de validação
├── contracts/
│   └── cli.md           # Contrato de interface e comandos da CLI
└── checklists/
    └── requirements.md  # Validação de conformidade dos requisitos
```

### Source Code Layout

```text
tools/ci/
├── go.mod                  # Módulo Go independente (ex: module contas/tools/ci)
├── go.sum                  # Checksums das dependências Go
├── cmd/
│   └── ci/
│       └── main.go         # Ponto de entrada da CLI (contas-ci)
└── internal/
    ├── config/
    │   ├── token.go        # Resolução de SONAR_TOKEN e prioridades
    │   └── token_test.go   # Testes unitários de resolução de tokens
    ├── runner/
    │   ├── executor.go     # Execução de comandos Python/uv com streaming
    │   └── executor_test.go# Testes unitários do executor
    ├── sonar/
    │   ├── client.go       # Cliente HTTP REST para API do SonarQube
    │   ├── scanner.go      # Disparo do container do SonarScanner (podman/docker)
    │   ├── quality_gate.go # Polling e avaliação do Quality Gate
    │   └── client_test.go  # Testes com mock HTTP server
    └── pipeline/
        ├── check.go        # Orquestrador do comando 'check' (lint, test, migration)
        └── all.go          # Orquestrador completo

# Integrações no repositório
.github/workflows/
└── ci.yml                  # Atualizado com jobs simplificados usando 'contas-ci'
sonar_check.sh              # Wrapper retrocompatível chamando 'go run ./tools/ci/cmd/ci sonar "$@"'
```

---

## Design Artifacts Summary

1. **Research & Decisions**: [`research.md`](research.md) ratifica Go 1.22+, `cobra`, cliente HTTP nativo para SonarQube e suporte a `podman`.
2. **Data Model**: [`data-model.md`](data-model.md) detalha `PipelineStep`, `PipelineResult`, `SonarConfig` e respostas de endpoints do SonarQube.
3. **Contracts**: [`contracts/cli.md`](contracts/cli.md) formaliza subcomandos (`check`, `lint`, `format-check`, `test`, `sonar`, `all`), flags e exit codes.
4. **Validation Guide**: [`quickstart.md`](quickstart.md) documenta cenários de teste locais e no GitHub Actions.

---

## Re-avaliação do Constitution Check Post-Design

Após o detalhamento do design:
- O layout isolado sob `tools/ci/` preserva a simplicidade do repositório Python.
- Nenhum princípio foi violado.
- Os requisitos de idioma (PT-BR em documentações, EN-US em código Go) foram integralmente respeitados.
- **Portão de Qualidade Arquitetural**: **APROVADO**. Pronto para a geração da lista ordenada de tarefas (`/speckit-tasks`).
