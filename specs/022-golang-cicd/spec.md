# Feature Specification: Migração e Unificação do CI/CD com Go Lang (022-golang-cicd)

**Feature Branch**: `feature/022-golang-cicd`

**Created**: 2026-11-14

**Status**: Ready for Planning

**Input**: User description: "vamos criar uma nova feature onde o CI/CD utilize Go Lang / vamos migrar o que temos agora no CI/CD para go lang"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execução e Orquestração Local Unificada do Pipeline (Priority: P1) 🎯 MVP

Como desenvolvedor trabalhando no projeto Contas,
Quero executar todas as validações de CI/CD (linter, formatação, migrations, testes e cobertura) localmente através de uma ferramenta CLI compilável em Go,
Para que eu obtenha feedback imediato, consistente e idêntico ao ambiente de integração contínua sem depender de múltiplos scripts Bash fragmentados.

**Why this priority**: Estabelece o núcleo executável da automação em Go (CLI autônoma), garantindo paridade total entre o ambiente local do desenvolvedor e os jobs remotos do CI com inicialização ultrarrápida e portabilidade.

**Independent Test**: Pode ser testado executando a CLI em Go (`go run ./cmd/ci ...` ou binário compilado) com subcomandos/flags para `lint`, `format-check` e `test`, verificando a execução orquestrada com logs claros e códigos de retorno apropriados.

**Acceptance Scenarios**:
1. **Given** que o desenvolvedor deseja validar o código antes do commit, **When** executa o pipeline via CLI Go (`contas-ci run all` ou `contas-ci check`), **Then** a ferramenta orquestra `ruff check`, validação de formatação e os testes com `pytest`, reportando progresso estruturado e retornando status 0 em caso de sucesso.
2. **Given** que há um arquivo fora das regras de linting ou com testes quebrados, **When** a ferramenta Go executa a etapa correspondente, **Then** ela interrompe a execução com código de saída diferente de zero, exibindo mensagem de erro amigável e diagnóstico da falha.
3. **Given** que o desenvolvedor deseja rodar apenas um subconjunto de etapas (ex: somente testes ou somente lint), **When** passa comandos específicos (`contas-ci lint`, `contas-ci test`), **Then** a ferramenta executa estritamente as etapas solicitadas.

---

### User Story 2 - Automação da Integração com SonarQube e Quality Gate em Go (Priority: P2)

Como engenheiro de software e mantenedor da qualidade do projeto,
Quero que as rotinas de verificação de conectividade, configuração de tokens, disparo do scanner e polling do Quality Gate do SonarQube sejam executadas pelo módulo em Go,
Para substituir o script `sonar_check.sh` por uma solução tipada, resiliente a falhas de rede, com parsing seguro de JSON e tratamento de concorrência.

**Why this priority**: O script `sonar_check.sh` atual possui 183 linhas com chamadas `curl`, parsing via inline Python e manipulação de shell sensível a variações de ambiente. Migrá-lo para Go garante confiabilidade, testes unitários para a própria automação e manutenibilidade.

**Independent Test**: Pode ser testado executando o subcomando de SonarQube (`contas-ci sonar`) contra o servidor SonarQube (local ou remoto em dc1), validando autenticação por token, inicialização do scanner e recebimento do status do Quality Gate (OK/ERROR).

**Acceptance Scenarios**:
1. **Given** um servidor SonarQube disponível e o `SONAR_TOKEN` configurado (via env, `.env` ou arquivo de token), **When** o subcomando Go `contas-ci sonar` é acionado, **Then** ele valida o token via cliente HTTP nativo em Go, orquestra a execução do SonarScanner e monitora a task até o veredito final do Quality Gate.
2. **Given** que o servidor SonarQube está temporariamente indisponível ou o token expirou, **When** o comando Go é iniciado, **Then** ele aplica retries com backoff exponencial e, persistindo a falha, encerra a execução com erro detalhado e sugestão de correção sem crashes inesperados.
3. **Given** divergências de formatação detectadas pelo SonarFormatter, **When** a ferramenta Go avalia o Quality Gate, **Then** ela correlaciona o status do SonarQube e o relatório de formatação antes de declarar a esteira aprovada.

---

### User Story 3 - Integração da CLI Go nos Workflows do GitHub Actions (Priority: P3)

Como mantenedor do repositório no GitHub,
Quero que os workflows do GitHub Actions (`.github/workflows/ci.yml`) utilizem os comandos da CLI em Go para os jobs de build, teste e verificação de qualidade do SonarQube,
Para simplificar a definição dos workflows YAML, eliminando blocos complexos de script inline e reduzindo o tempo de execução no CI, mantendo as automações de PR e Release gerenciadas pelas actions nativas do GitHub.

**Why this priority**: Fecha o ciclo de vida do CI/CD, garantindo que o pipeline remoto no GitHub seja apenas uma casca simples que delega a lógica de validação para a CLI em Go.

**Independent Test**: Pode ser testado disparando o workflow do GitHub Actions em um branch de feature, verificando se os jobs utilizam a CLI Go e se os artefatos de cobertura e relatórios de qualidade são gerados e validados com sucesso.

**Acceptance Scenarios**:
1. **Given** um push em branch `feature/*` ou `develop`, **When** o GitHub Actions executa o pipeline, **Then** o workflow invoca os comandos da CLI Go (`contas-ci check` e `contas-ci sonar`), executando build, testes e SonarQube de forma consistente.
2. **Given** a conclusão com sucesso de todos os passos de validação da CLI Go, **When** o workflow avança para as etapas subsequentes, **Then** as actions nativas existentes de Pull Request e Release no GitHub são executadas normalmente.

---

### Edge Cases

- **Ausência de Go no ambiente do desenvolvedor**: O repositório deve fornecer suporte para execução direta via `go run` no diretório da CLI ou compilação de binário local (`go build -o bin/contas-ci ./cmd/ci`), além de documentação clara de pré-requisitos.
- **Falha intermitente de rede com a API do SonarQube**: A implementação em Go deve implementar timeout configurável e retries com backoff exponencial nativo em Go, em vez de repetições e sleeps estáticos de shell.
- **Diferenças de caminhos de arquivos entre host e container**: A CLI em Go deve realizar a normalização determinística dos caminhos de arquivos de cobertura (`coverage.xml` e caminhos do SonarScanner) entre a máquina host e o container.
- **Detecção de engine de container (Podman vs Docker)**: A CLI em Go deve inspecionar automaticamente a disponibilidade de `podman` ou `docker` no sistema para invocar o SonarScanner no ambiente apropriado.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE disponibilizar uma CLI autônoma e modular em Go (localizada em `cmd/ci` com pacote em `pkg/ci` ou `internal/ci`), gerando um executável unificado (`contas-ci`).
- **FR-002**: A CLI Go DEVE implementar comandos modulares para as etapas do pipeline:
  - `contas-ci lint`: executa a validação de regras de código via `ruff check`.
  - `contas-ci format-check`: valida conformidade de formatação e gera relatórios para SonarQube.
  - `contas-ci test`: orquestra as migrações do banco e a execução dos testes com geração de cobertura (`coverage.xml`).
  - `contas-ci sonar`: executa o ciclo completo de análise SonarQube e Quality Gate.
  - `contas-ci all`: executa todas as etapas em sequência ordenada.
- **FR-003**: A CLI Go DEVE orquestrar ferramentas Python do ecossistema do projeto (`uv`, `ruff`, `pytest`, `alembic`), capturando saídas de forma estruturada.
- **FR-004**: A CLI Go DEVE substituir integralmente as 183 linhas do script `sonar_check.sh`, incluindo verificação de status UP, validação e resolução de `SONAR_TOKEN`, criação de projeto/profile, execução do container scanner e polling assíncrono do Quality Gate.
- **FR-005**: A CLI Go DEVE consultar a API REST do SonarQube utilizando cliente HTTP nativo em Go com tratamento explícito de erros, timeouts e retries.
- **FR-006**: A CLI Go DEVE seguir estritamente a política de prioridade do `SONAR_TOKEN`:
  1. Variável de ambiente `SONAR_TOKEN`
  2. Arquivo `.env` na raiz do projeto
  3. Arquivo `.sonar_token`
  4. Arquivo `.sonar_remote_token`
- **FR-007**: A CLI Go DEVE ser integrada ao `.github/workflows/ci.yml`, substituindo os blocos de scripts Bash inline nos jobs de teste e SonarQube.
- **FR-008**: O escopo de automação de Pull Requests (`auto-pr-to-develop`, `auto-pr-to-main`) e Releases (`release-on-main`) DEVE permanecer sob responsabilidade das actions e steps nativos do GitHub Actions, recebendo o sinal de sucesso dos jobs validados pela CLI Go.
- **FR-009**: A CLI Go DEVE retornar códigos de saída padronizados no padrão POSIX (`0` para sucesso e `!= 0` para falhas), garantindo interrupção correta nos runners de CI.

---

### Key Entities *(include if feature involves data)*

- **PipelineStep**: Representa uma etapa executável do pipeline (ex: `lint`, `format-check`, `migration`, `test`, `sonar`). Atributos: `Name`, `Description`, `Command`, `Args`, `EnvVars`, `Timeout`, `Required`.
- **PipelineResult**: Estrutura com o resultado da execução de cada etapa. Atributos: `StepName`, `Status` (Success/Failed/Skipped), `Duration`, `StdOut`, `StdErr`, `ExitCode`.
- **SonarConfig**: Parâmetros de conexão e autenticação do SonarQube. Atributos: `HostURL`, `Token`, `ProjectKey`, `ContainerEngine`, `QualityProfile`, `QualityGateStatus`, `PollingInterval`, `MaxRetries`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das funcionalidades atualmente executadas pelo script `sonar_check.sh` (183 linhas) são migradas e executadas com sucesso pela CLI em Go.
- **SC-002**: Redução de pelo menos 40% na quantidade de linhas de scripts Bash inline em `.github/workflows/ci.yml`.
- **SC-003**: O pipeline completo ou qualquer de seus subcomandos inicia em menos de 100 milissegundos a partir do disparo do comando compilado.
- **SC-004**: 100% dos testes e análises de qualidade podem ser reproduzidos na máquina do desenvolvedor com exatamente os mesmos comandos e comportamentos do GitHub Actions.
- **SC-005**: Tratamento resiliente a falhas na API do SonarQube com timeouts claros e mensagens de diagnóstico amigáveis, eliminando loops infinitos ou silent failures.

---

## Assumptions

- O ambiente de desenvolvimento e os runners do GitHub Actions possuem Go 1.22+ ou 1.23+ disponível.
- A aplicação Python principal (`src/contas`) permanece inalterada em sua arquitetura; o código em Go ficará isolado em pasta de ferramentas/CI (ex: `tools/ci` ou `cmd/ci`).
- As dependências Python do projeto continuarão sendo gerenciadas via `uv`.
- A integração com SonarQube continuará utilizando o SonarScanner via container (`podman` ou `docker`) apontando para o servidor configurado (`SONAR_HOST_URL`).
