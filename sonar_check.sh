#!/usr/bin/env bash
# ==============================================================================
# Script: sonar_check.sh
# Finalidade: 
#   Executa a validação de qualidade contra o servidor SonarQube no dc1 (192.168.1.20)
#   ou fallback local se customizado.
#   1. Garante conectividade com o SonarQube em $SONAR_HOST_URL
#   2. Executa os testes unitários com cobertura via pytest
#   3. Executa o SonarScanner localmente via Podman apontando para o servidor dc1
#   4. Valida o Quality Gate e exibe os resultados
# ==============================================================================

set -euo pipefail

PROJECT_KEY="contas"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detecta engine de container (podman ou docker)
CONTAINER_ENGINE="podman"
if ! command -v podman &> /dev/null; then
    CONTAINER_ENGINE="docker"
fi

# Seleciona o servidor SonarQube (padrão dc1 na rede local, ou customizado via SONAR_HOST_URL)
SONAR_HOST_URL="${SONAR_HOST_URL:-http://192.168.1.20:9000}"

echo "=========================================================="
echo "🛡️  Executando análise SonarQube ($SONAR_HOST_URL via $CONTAINER_ENGINE)"
echo "=========================================================="

# 1. Garante que o SonarQube está acessível
echo "⏳ Verificando status do SonarQube em $SONAR_HOST_URL..."
STATUS="DOWN"
for i in {1..3}; do
    STATUS=$(curl -s --connect-timeout 2 "$SONAR_HOST_URL/api/system/status" | grep -Po '"status":"\K[^"]*' || echo "DOWN")
    if [ "$STATUS" = "UP" ]; then
        echo "✅ Servidor SonarQube pronto para análise!"
        break
    fi
    sleep 1
done

if [ "$STATUS" != "UP" ]; then
    echo "❌ Erro: Não foi possível conectar ao SonarQube em $SONAR_HOST_URL."
    echo "Certifique-se de que o servidor dc1 (192.168.1.20:9000) está ativo."
    exit 1
fi

# 2. Configura autenticação priorizando o SONAR_TOKEN (env -> .env -> .sonar_remote_token)
SONAR_TOKEN_FILE="$PROJECT_DIR/.sonar_remote_token"

if [ -z "${SONAR_TOKEN:-}" ] && [ -f "$PROJECT_DIR/.env" ]; then
    ENV_SONAR_TOKEN=$(grep -E '^SONAR_TOKEN=' "$PROJECT_DIR/.env" | tail -n 1 | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
    if [ -n "$ENV_SONAR_TOKEN" ]; then
        SONAR_TOKEN="$ENV_SONAR_TOKEN"
    fi
fi

if [ -z "${SONAR_TOKEN:-}" ] && [ -f "$PROJECT_DIR/.sonar_token" ]; then
    SONAR_TOKEN=$(tr -d '[:space:]' < "$PROJECT_DIR/.sonar_token")
fi

if [ -z "${SONAR_TOKEN:-}" ] && [ -f "$SONAR_TOKEN_FILE" ]; then
    SONAR_TOKEN=$(tr -d '[:space:]' < "$SONAR_TOKEN_FILE")
fi

if [ -z "${SONAR_TOKEN:-}" ]; then
    echo "❌ Erro: SONAR_TOKEN não encontrado (defina SONAR_TOKEN no ambiente, no .env ou em .sonar_remote_token)."
    exit 1
fi

VALID=$(curl -s -u "${SONAR_TOKEN}:" "$SONAR_HOST_URL/api/authentication/validate" | grep -Po '"valid":\K(true|false)' || echo "false")
if [ "$VALID" != "true" ]; then
    echo "❌ Erro: O SONAR_TOKEN informado é inválido ou expirou em $SONAR_HOST_URL."
    exit 1
fi

# Persiste no arquivo local com permissão restrita para reutilização
echo "$SONAR_TOKEN" > "$SONAR_TOKEN_FILE"
chmod 600 "$SONAR_TOKEN_FILE"

# Garante que o projeto exista usando o SONAR_TOKEN
curl -s -u "${SONAR_TOKEN}:" -X POST "$SONAR_HOST_URL/api/projects/create?name=$PROJECT_KEY&project=$PROJECT_KEY" > /dev/null 2>&1 || true

# 2.1 Configura Quality Profile no SonarQube com regra de formatação ativa usando o SONAR_TOKEN
echo "📐 Configurando regras de Formatter no Quality Profile do SonarQube..."
PROFILE_NAME="Contas Python (Sonar way + Formatter)"
curl -s -u "${SONAR_TOKEN}:" -X POST "$SONAR_HOST_URL/api/qualityprofiles/create" \
    --data-urlencode "language=py" \
    --data-urlencode "name=$PROFILE_NAME" > /dev/null 2>&1 || true

curl -s -u "${SONAR_TOKEN}:" -X POST "$SONAR_HOST_URL/api/qualityprofiles/change_parent" \
    --data-urlencode "language=py" \
    --data-urlencode "qualityProfile=$PROFILE_NAME" \
    --data-urlencode "parentQualityProfile=Sonar way" > /dev/null 2>&1 || true

PROFILE_KEY=$(curl -s -u "${SONAR_TOKEN}:" "$SONAR_HOST_URL/api/qualityprofiles/search?language=py" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('profiles', []):
    if p.get('name') == '$PROFILE_NAME':
        print(p.get('key', ''))
        break
" 2>/dev/null || echo "")

if [ -n "$PROFILE_KEY" ]; then
    # Ativa regra de formatação de fim de arquivo (python:S113) no perfil do SonarQube
    # ( somada à regra ruff-formatter:unformatted-file via sonar.externalIssuesReportPaths )
    curl -s -u "${SONAR_TOKEN}:" -X POST "$SONAR_HOST_URL/api/qualityprofiles/activate_rule" \
        --data-urlencode "key=$PROFILE_KEY" \
        --data-urlencode "rule=python:S113" \
        --data-urlencode "severity=MAJOR" > /dev/null 2>&1 || true

    curl -s -u "${SONAR_TOKEN}:" -X POST "$SONAR_HOST_URL/api/qualityprofiles/add_project" \
        --data-urlencode "language=py" \
        --data-urlencode "qualityProfile=$PROFILE_NAME" \
        --data-urlencode "project=$PROJECT_KEY" > /dev/null 2>&1 || true
fi

# 3. Executa verificação de Formatter (Ruff Format + Ruff Check) e gera relatórios para o SonarQube
echo "🎨 Verificando formatação (Ruff Formatter) e gerando relatórios para o SonarQube..."
cd "$PROJECT_DIR"
FORMATTER_STATUS=0
python3 .agents/skills/formatter/scripts/sonar_formatter_check.py --container-prefix /usr/src || FORMATTER_STATUS=$?

# 4. Executa os testes locais com cobertura
echo "🧪 Executando testes unitários e gerando relatório de cobertura..."
uv run pytest -v tests/ --cov=src/contas --cov-report=xml:coverage.xml

# Ajusta caminhos no coverage.xml para mapear com o container do scanner
sed -i "s|/home/cristiano/Dev/contas/src|/usr/src/src|g" coverage.xml

# 5. Roda a análise com SonarScanner apontando para dc1
echo "🔍 Executando SonarScanner apontando para $SONAR_HOST_URL..."
$CONTAINER_ENGINE run --rm \
    -v "$PROJECT_DIR:/usr/src:Z" \
    --network host \
    docker.io/sonarsource/sonar-scanner-cli:latest \
    -Dsonar.host.url="$SONAR_HOST_URL" \
    -Dsonar.token="$SONAR_TOKEN" \
    -Dsonar.projectKey="$PROJECT_KEY" \
    -Dsonar.sources=src \
    -Dsonar.tests=tests \
    -Dsonar.python.coverage.reportPaths=coverage.xml \
    -Dsonar.python.ruff.reportPaths=ruff-report.json \
    -Dsonar.externalIssuesReportPaths=sonar-formatter-issues.json \
    -Dsonar.exclusions="**/__pycache__/**,**/*.pyc,**/.venv/**,**/alembic/versions/**,**/docker/keycloak/**" \
    -Dsonar.coverage.exclusions="tests/**,**/alembic/**,**/__init__.py,**/ui/app.py,**/ui/views/**,**/__main__.py"

# 6. Avaliação do Quality Gate
echo "🚦 Aguardando processamento da análise no servidor SonarQube..."
for i in {1..30}; do
    CE_STATUS=$(curl -s -u "${SONAR_TOKEN}:" "$SONAR_HOST_URL/api/ce/component?component=$PROJECT_KEY" | grep -Po '"status":"\K[^"]*' || echo "")
    if [ "$CE_STATUS" = "SUCCESS" ] || [ -z "$CE_STATUS" ]; then
        break
    fi
    sleep 2
done

QG_STATUS=$(curl -s -u "${SONAR_TOKEN}:" "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=$PROJECT_KEY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('projectStatus', {}).get('status', 'ERROR'))" 2>/dev/null || echo "ERROR")

echo "=========================================================="
if [ "$QG_STATUS" = "OK" ] && [ "$FORMATTER_STATUS" -eq 0 ]; then
    echo "🎉 SUCESSO: Quality Gate e Regra de Formatter APROVADOS no dc1! Código limpo e validado."
    echo "Dashboard: $SONAR_HOST_URL/dashboard?id=$PROJECT_KEY"
    echo "=========================================================="
    exit 0
else
    echo "🛑 FALHA: Quality Gate ($QG_STATUS) ou Regra de Formatter (exit=$FORMATTER_STATUS) REPROVADO."
    echo "Existem arquivos fora de formatação, vulnerabilidades, bugs ou cobertura insuficiente."
    echo "Execute '.venv/bin/ruff format .' e consulte o dashboard: $SONAR_HOST_URL/dashboard?id=$PROJECT_KEY"
    echo "=========================================================="
    exit 1
fi

