#!/usr/bin/env bash
# ==============================================================================
# Script: sonar_check.sh
# Finalidade: 
#   Wrapper para a ferramenta de CI em Go (contas-ci).
#   Suporta execução direta do binário compilado ou via container Podman local.
# ==============================================================================

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="$PROJECT_DIR/bin/contas-ci"

# 1. Se o binário compilado existir, executa-o diretamente
if [ -x "$BIN_PATH" ]; then
    exec "$BIN_PATH" sonar --dir "$PROJECT_DIR" "$@"
fi

# 2. Se Go estiver disponível no PATH, executa via 'go run'
if command -v go &> /dev/null; then
    cd "$PROJECT_DIR/tools/ci"
    exec go run ./cmd/ci sonar --dir "$PROJECT_DIR" "$@"
fi

# 3. Caso contrário, executa dentro do container Podman oficial do Go
echo "🐳 [contas-ci] Executando análise através do container Podman Go (golang:1.23-alpine)..."
exec "$PROJECT_DIR/tools/ci/run_in_container.sh" sh -c "cd tools/ci && go run ./cmd/ci sonar --dir /workspace \"\$@\"" -- "$@"
