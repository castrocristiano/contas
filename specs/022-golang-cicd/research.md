# Research & Technical Decisions: Ferramenta de CI/CD em Go Lang (022-golang-cicd)

**Feature**: `022-golang-cicd`  
**Data**: 2026-11-14  
**Status**: Concluído (Decisões Ratificadas)

---

## 1. Arquitetura da Ferramenta e Framework CLI em Go

### Decisão
Criar uma CLI modular em Go localizada no diretório `tools/ci`, com ponto de entrada em `tools/ci/cmd/ci/main.go` e pacotes internos sob `tools/ci/internal/...`. A CLI utilizará `spf13/cobra` para estruturação de subcomandos legíveis, flags tipadas e mensagens de ajuda padronizadas.

### Racional
- **Isolamento de Domínio**: O repositório Contas é primordialmente Python (`src/contas`). O código Go deve ter seu próprio `go.mod` em `tools/ci/go.mod`, evitando misturar dependências com o workspace Python e permitindo compilação independente.
- **Portabilidade**: Com Go, compilamos um binário estático e autocontido (`contas-ci`) ou rodamos diretamente em tempo de execução via `go run ./cmd/ci <subcomando>`.
- **Experiência do Desenvolvedor (DX)**: Cobra fornece suporte nativo a subcomandos claros (`lint`, `test`, `sonar`, `check`), flags globais (ex: `--verbose`, `--sonar-url`, `--token`) e help messages automáticas.

### Alternativas Consideradas
- **Go padrão com pacote `flag`**: Embora não adicione dependências externas, o pacote `flag` padrão da biblioteca Go torna a criação de múltiplos subcomandos aninhados verbosa e propensa a boilerplate manual.
- **Magefile (`mage`)**: Requer que o desenvolvedor tenha o binário `mage` instalado ou compile o runner do Mage previamente. Adiciona uma camada de abstração que mascara a chamada direta de comandos.
- **Dagger Go SDK**: Exige o daemon Dagger em execução, aumentando a sobrecarga de memória e o tempo de inicialização em máquinas locais com recursos limitados.

---

## 2. Orquestração de Execução de Processos e Ferramentas Python

### Decisão
Implementar um pacote executor (`tools/ci/internal/runner`) usando o pacote padrão `os/exec` com streaming de `stdout`/`stderr` em tempo real e captura de saída bufferizada para diagnósticos em caso de falha.

### Racional
- **Feedback Imediato**: Durante testes unitários longos (`pytest`) ou upgrades de banco (`alembic`), o desenvolvedor precisa ver o progresso linha a linha no console, e não esperar o término do comando para ver uma tela estática.
- **Cancelamento e Timeout**: Uso de `context.WithTimeout` para garantir que comandos que travarem (ex: conexões pendentes de rede) sejam finalizados de forma controlada sem gerar processos zumbis.
- **Detecção de Ambiente**: O executor inspecionará a presença de `uv` no sistema, caindo de forma resiliente para binários no `.venv/bin/` ou no `PATH`.

### Alternativas Consideradas
- **Execução via Shell Wrapper (`sh -c ...`)**: Aumenta o risco de injeção de comandos e diferenças de comportamento entre interpretadores de shell (dash, bash, zsh). O uso direto de `exec.CommandContext` com argumentos explícitos (`slice` de strings) elimina vulnerabilidades e comportamentos anômalos de escape.

---

## 3. Cliente HTTP e Integração Nativa com SonarQube API

### Decisão
Implementar um cliente HTTP nativo em Go (`tools/ci/internal/sonar/client.go`) utilizando `net/http` da biblioteca padrão com autenticação HTTP Basic (passando `token:` como credencial), suporte a retries com backoff exponencial e decodificação tipada de JSON para os seguintes endpoints:
- `GET /api/system/status`: Health check do servidor com polling até estado `UP`.
- `GET /api/authentication/validate`: Validação prévia de validade e expiração do `SONAR_TOKEN`.
- `POST /api/projects/create`: Criação idempotente do projeto `contas` se inexistente.
- `GET /api/qualityprofiles/search` e `POST /api/qualityprofiles/*`: Configuração de Quality Profile e regras de formatação.
- `GET /api/ce/component`: Monitoramento do processamento da análise do scanner.
- `GET /api/qualitygates/project_status`: Avaliação do Quality Gate final (`OK` ou `ERROR`).

### Racional
- **Eliminação de Frigidez do Shell**: No `sonar_check.sh`, 183 linhas continham interpolações frágeis de curl, regex via `grep -Po` e chamadas one-liner `python3 -c "import sys, json..."`. Em Go, respostas JSON são desserializadas diretamente em structs com tipagem estática e tratamento de erro de parsing.
- **Resiliência a Instabilidades de Rede**: A API do SonarQube pode levar segundos para responder após a inicialização de containers. Um cliente HTTP nativo com retries exponenciais configuráveis elimina sleeps estáticos desnecessários.

---

## 4. Execução do SonarScanner e Compatibilidade de Containers

### Decisão
A CLI Go detectará automaticamente a engine de container disponível (`podman` preferencialmente, com fallback para `docker`) e executará a imagem oficial `docker.io/sonarsource/sonar-scanner-cli:latest`. Antes do scanner, a CLI Go ajustará os caminhos relativos no arquivo de cobertura (`coverage.xml`), substituindo caminhos absolutos do host pelo prefixo `/usr/src/` do container.

### Racional
- Mantém total compatibilidade com o princípio **V da Constituição** (`podman-compose` e Podman rootless).
- Evita a necessidade de instalar Java Runtime Environment (JRE) ou o binário do SonarScanner nativamente no host da máquina local ou nas imagens do CI.

---

## 5. Resolução Segura de Credenciais e Prioridade de Tokens

### Decisão
A CLI Go seguirá estritamente a política de prioridade do `SONAR_TOKEN`:
1. Variável de ambiente `SONAR_TOKEN` (já presente no processo).
2. Variável `SONAR_TOKEN` no arquivo `.env` da raiz do repositório.
3. Arquivo `.sonar_token` na raiz do repositório.
4. Arquivo `.sonar_remote_token` na raiz do repositório.

Se nenhum token for encontrado, a CLI Go exibirá instruções amigáveis sem expor nenhum segredo e finalizará com exit code `1`.
