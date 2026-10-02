#!/usr/bin/env bash
# ==============================================================================
# Script: sonar_check.sh
# Finalidade: 
#   Roda localmente na sua máquina de desenvolvimento:
#   1. Sobe o container local do SonarQube Community Edition (porta 9000)
#   2. Executa os testes com pytest e gera coverage.xml
#   3. Executa o SonarScanner localmente
#   4. Valida o Quality Gate e barra o fluxo se houver faltas graves
# ==============================================================================

set -euo pipefail

PROJECT_KEY="contas"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SONAR_CONTAINER="sonarqube-local"
SONAR_PORT="9000"

# Detecta engine de container (podman ou docker)
CONTAINER_ENGINE="podman"
if ! command -v podman &> /dev/null; then
    CONTAINER_ENGINE="docker"
fi

echo "=========================================================="
echo "🛡️  Executando SonarQube na máquina de desenvolvimento ($CONTAINER_ENGINE)"
echo "=========================================================="

# 1. Garante que o SonarQube está rodando localmente
if ! $CONTAINER_ENGINE ps --format "{{.Names}}" | grep -q "^${SONAR_CONTAINER}$"; then
    if $CONTAINER_ENGINE ps -a --format "{{.Names}}" | grep -q "^${SONAR_CONTAINER}$"; then
        echo "Iniciando container SonarQube existente..."
        $CONTAINER_ENGINE start "$SONAR_CONTAINER"
    else
        echo "Iniciando novo container SonarQube Community..."
        $CONTAINER_ENGINE run -d \
            --name "$SONAR_CONTAINER" \
            -p "${SONAR_PORT}:9000" \
            -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
            docker.io/library/sonarqube:10.5-community
    fi
fi

# 2. Aguarda o SonarQube ficar pronto
echo "⏳ Aguardando SonarQube responder em http://localhost:$SONAR_PORT..."
for i in {1..40}; do
    STATUS=$(curl -s "http://localhost:$SONAR_PORT/api/system/status" | grep -Po '"status":"\K[^"]*' || echo "DOWN")
    if [ "$STATUS" = "UP" ]; then
        echo "✅ SonarQube pronto para análise!"
        break
    fi
    sleep 3
done

# 3. Configura autenticação e token seguro
SONAR_TOKEN_FILE="$PROJECT_DIR/.sonar_remote_token"
if [ ! -f "$SONAR_TOKEN_FILE" ]; then
    echo "🔑 Configurando credenciais locais..."
    curl -s -u admin:admin -X POST "http://localhost:$SONAR_PORT/api/users/change_password?login=admin&previousPassword=admin&password=admin1234" > /dev/null 2>&1 || true
    curl -s -u admin:admin1234 -X POST "http://localhost:$SONAR_PORT/api/projects/create?name=$PROJECT_KEY&project=$PROJECT_KEY" > /dev/null 2>&1 || true
    
    TOKEN_RESP=$(curl -s -u admin:admin1234 -X POST "http://localhost:$SONAR_PORT/api/user_tokens/generate?name=local-$(date +%s)")
    TOKEN=$(echo "$TOKEN_RESP" | grep -Po '"token":"\K[^"]*' || echo "")
    if [ -n "$TOKEN" ]; then
        echo "$TOKEN" > "$SONAR_TOKEN_FILE"
    else
        echo "admin1234" > "$SONAR_TOKEN_FILE"
    fi
    chmod 600 "$SONAR_TOKEN_FILE"
fi

SONAR_TOKEN=$(cat "$SONAR_TOKEN_FILE")

# 4. Executa os testes locais com cobertura
echo "🧪 Executando testes unitários e gerando relatório de cobertura..."
cd "$PROJECT_DIR"
uv run pytest -v tests/unit --cov=src/contas --cov-report=xml:coverage.xml

# 5. Roda a análise com SonarScanner
echo "🔍 Executando SonarScanner..."
$CONTAINER_ENGINE run --rm \
    -v "$PROJECT_DIR:/usr/src:Z" \
    --network host \
    docker.io/sonarsource/sonar-scanner-cli:latest \
    -Dsonar.host.url="http://localhost:$SONAR_PORT" \
    -Dsonar.token="$SONAR_TOKEN" \
    -Dsonar.projectKey="$PROJECT_KEY" \
    -Dsonar.sources=src \
    -Dsonar.tests=tests \
    -Dsonar.python.coverage.reportPaths=coverage.xml \
    -Dsonar.exclusions="**/__pycache__/**,**/*.pyc,**/.venv/**,**/alembic/versions/**" \
    -Dsonar.coverage.exclusions="tests/**,**/alembic/**,**/__init__.py"

# 6. Avaliação do Quality Gate
echo "🚦 Consultando Quality Gate..."
sleep 3
QG_STATUS=$(curl -s -u "${SONAR_TOKEN}:" "http://localhost:$SONAR_PORT/api/qualitygates/project_status?projectKey=$PROJECT_KEY" | grep -Po '"status":"\K[^"]*' || echo "ERROR")

echo "=========================================================="
if [ "$QG_STATUS" = "OK" ]; then
    echo "🎉 SUCESSO: Quality Gate APROVADO! Código limpo e validado."
    echo "Dashboard: http://localhost:$SONAR_PORT/dashboard?id=$PROJECT_KEY"
    echo "=========================================================="
    exit 0
else
    echo "🛑 FALHA: Quality Gate REPROVADO (Status: $QG_STATUS)."
    echo "Existem vulnerabilidades, bugs graves ou cobertura insuficiente."
    echo "Consulte o dashboard para corrigir: http://localhost:$SONAR_PORT/dashboard?id=$PROJECT_KEY"
    echo "=========================================================="
    exit 1
fi
