#!/usr/bin/env bash
# ==============================================================================
# Script: run_in_container.sh
# Finalidade:
#   Executa comandos Go ou a ferramenta de CI dentro do container Podman oficial
#   (docker.io/library/golang:1.23-alpine) sem necessidade de ter Go instalado
#   no host local.
# ==============================================================================

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Detecta engine de container (podman preferencialmente)
CONTAINER_ENGINE="podman"
if ! command -v podman &> /dev/null; then
    if command -v docker &> /dev/null; then
        CONTAINER_ENGINE="docker"
    else
        echo "❌ Erro: Podman (ou Docker) não encontrado para executar o container Go."
        exit 1
    fi
fi

IMAGE="docker.io/library/golang:1.23-alpine"

exec "$CONTAINER_ENGINE" run --rm \
    -v "$PROJECT_DIR:/workspace:Z" \
    -w /workspace \
    --network host \
    "$IMAGE" "$@"
