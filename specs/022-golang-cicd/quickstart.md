# Quickstart & Guia de Validação: CLI de CI/CD em Go (022-golang-cicd)

**Feature**: `022-golang-cicd`  
**Data**: 2026-11-14  
**Status**: Concluído

Este guia fornece instruções diretas para compilar, executar e validar a ferramenta `contas-ci` em ambiente local e no CI.

---

## 1. Pré-Requisitos

- **Go**: Versão 1.22 ou superior instalada (`go version`).
- **Python / uv**: `uv` instalado e dependências sincronizadas (`uv sync`).
- **Container Engine**: `podman` ou `docker` ativo para execução do SonarScanner.
- **Servidor SonarQube**: Acessível em `SONAR_HOST_URL` (ex: `http://192.168.1.20:9000` ou container local).

---

## 2. Cenário 1: Compilação e Execução Básica de Checagem

### Passo 1: Compilar a CLI ou executar via `go run`
```bash
# Execução direta via go run
go run ./tools/ci/cmd/ci --help

# Ou compilar o binário
cd tools/ci && go build -o ../../bin/contas-ci ./cmd/ci && cd ../..
./bin/contas-ci --help
```
**Resultado Esperado**: Exibição da ajuda da CLI com os subcomandos `check`, `lint`, `format-check`, `test`, `sonar` e `all`.

---

## 3. Cenário 2: Validação Estática e Testes Locais (`contas-ci check`)

```bash
./bin/contas-ci check
```
**Etapas Executadas**:
1. Validação com `ruff check .`
2. Validação de formatação e relatórios do SonarFormatter
3. Execução de migrações (`alembic upgrade head`) se PostgreSQL estiver ativo
4. Execução de testes unitários com medição de cobertura (`pytest --cov=src/contas`)

**Resultado Esperado**:
- Todas as etapas executadas com indicação de progresso visual.
- Arquivo `coverage.xml` e relatórios de formatação gerados na raiz.
- Código de retorno `0`.

---

## 4. Cenário 3: Validação do SonarQube e Quality Gate (`contas-ci sonar`)

```bash
# Executa a análise apontando para o servidor dc1 ou local
./bin/contas-ci sonar --sonar-url "http://192.168.1.20:9000"
```
**Etapas Executadas**:
1. Health check HTTP do SonarQube com polling até status `UP`.
2. Resolução e validação do `SONAR_TOKEN`.
3. Configuração de Quality Profile e regras de formatação ativas.
4. Ajuste dos caminhos no `coverage.xml`.
5. Disparo do SonarScanner via Podman/Docker.
6. Polling do Quality Gate até conclusão da análise.

**Resultado Esperado**:
- Exibição de: `🎉 SUCESSO: Quality Gate e Regra de Formatter APROVADOS!`.
- Código de retorno `0`.

---

## 5. Cenário 4: Validação no GitHub Actions

No arquivo `.github/workflows/ci.yml`, o job `build-and-test` e o job `sonarqube` passam a utilizar:
```yaml
- name: Set up Go
  uses: actions/setup-go@v5
  with:
    go-version: '1.22'

- name: Run Build and Test via Go CI CLI
  run: go run ./tools/ci/cmd/ci check

- name: Run SonarQube Scan and Quality Gate via Go CI CLI
  run: go run ./tools/ci/cmd/ci sonar --sonar-url "http://localhost:9000"
```
**Resultado Esperado**: Workflow limpo, sem dezenas de linhas de scripts bash inline, reproduzível de forma idêntica entre local e CI.
