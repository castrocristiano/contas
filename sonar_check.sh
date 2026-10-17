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

# Seleciona o servidor SonarQube (preferência dc1 na rede local, ou localhost/CI)
if [ -z "${SONAR_HOST_URL:-}" ]; then
    if curl -s --connect-timeout 2 "http://192.168.1.20:9000/api/system/status" > /dev/null 2>&1; then
        SONAR_HOST_URL="http://192.168.1.20:9000"
    else
        SONAR_HOST_URL="http://localhost:9000"
    fi
fi

echo "=========================================================="
echo "🛡️  Executando análise SonarQube ($SONAR_HOST_URL via $CONTAINER_ENGINE)"
echo "=========================================================="

# 1. Garante que o SonarQube está acessível
echo "⏳ Verificando status do SonarQube em $SONAR_HOST_URL..."
for i in {1..30}; do
    STATUS=$(curl -s --connect-timeout 2 "$SONAR_HOST_URL/api/system/status" | grep -Po '"status":"\K[^"]*' || echo "DOWN")
    if [ "$STATUS" = "UP" ]; then
        echo "✅ Servidor SonarQube pronto para análise!"
        break
    fi
    sleep 2
done

if [ "$STATUS" != "UP" ]; then
    echo "❌ Erro: Não foi possível conectar ao SonarQube em $SONAR_HOST_URL."
    echo "Certifique-se de que o servidor dc1 (192.168.1.20:9000) está ativo."
    exit 1
fi

# 2. Configura autenticação e token seguro
SONAR_TOKEN_FILE="$PROJECT_DIR/.sonar_remote_token"
if [ -n "${SONAR_TOKEN:-}" ]; then
    echo "$SONAR_TOKEN" > "$SONAR_TOKEN_FILE"
    chmod 600 "$SONAR_TOKEN_FILE"
fi

if [ -f "$SONAR_TOKEN_FILE" ]; then
    CANDIDATE_TOKEN=$(cat "$SONAR_TOKEN_FILE")
    VALID=$(curl -s -u "${CANDIDATE_TOKEN}:" "$SONAR_HOST_URL/api/authentication/validate" | grep -Po '"valid":\K(true|false)' || echo "false")
    if [ "$VALID" != "true" ]; then
        rm -f "$SONAR_TOKEN_FILE"
    fi
fi

if [ ! -f "$SONAR_TOKEN_FILE" ]; then
    echo "🔑 Configurando credenciais no servidor SonarQube ($SONAR_HOST_URL)..."
    # Tenta criar projeto se não existir
    curl -s -u admin:Admin12345678! -X POST "$SONAR_HOST_URL/api/projects/create?name=$PROJECT_KEY&project=$PROJECT_KEY" > /dev/null 2>&1 || true
    
    TOKEN_RESP=$(curl -s -u admin:Admin12345678! -X POST "$SONAR_HOST_URL/api/user_tokens/generate?name=contas-$(date +%s)" 2>/dev/null || echo "")
    TOKEN=$(echo "$TOKEN_RESP" | grep -Po '"token":"\K[^"]*' || echo "")
    if [ -n "$TOKEN" ]; then
        echo "$TOKEN" > "$SONAR_TOKEN_FILE"
    else
        echo "Admin12345678!" > "$SONAR_TOKEN_FILE"
    fi
    chmod 600 "$SONAR_TOKEN_FILE"
fi

SONAR_TOKEN=$(cat "$SONAR_TOKEN_FILE")

# 3. Executa os testes locais com cobertura
echo "🧪 Executando testes unitários e gerando relatório de cobertura..."
cd "$PROJECT_DIR"
uv run pytest -v tests/ --cov=src/contas --cov-report=xml:coverage.xml

# Ajusta caminhos no coverage.xml para mapear com o container do scanner
sed -i "s|/home/cristiano/Dev/contas/src|/usr/src/src|g" coverage.xml

# 4. Roda a análise com SonarScanner apontando para dc1
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
    -Dsonar.exclusions="**/__pycache__/**,**/*.pyc,**/.venv/**,**/alembic/versions/**" \
    -Dsonar.coverage.exclusions="tests/**,**/alembic/**,**/__init__.py,**/ui/app.py,**/__main__.py"

# 5. Avaliação do Quality Gate
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
if [ "$QG_STATUS" = "OK" ]; then
    echo "🎉 SUCESSO: Quality Gate APROVADO no dc1! Código limpo e validado."
    echo "Dashboard: $SONAR_HOST_URL/dashboard?id=$PROJECT_KEY"
    echo "=========================================================="
    exit 0
else
    echo "🛑 FALHA: Quality Gate REPROVADO (Status: $QG_STATUS)."
    echo "Existem vulnerabilidades, bugs graves ou cobertura insuficiente."
    echo "Consulte o dashboard para corrigir: $SONAR_HOST_URL/dashboard?id=$PROJECT_KEY"
    echo "=========================================================="
    exit 1
fi
