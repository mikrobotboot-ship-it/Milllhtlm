#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PORT="${PORT:-8765}"
echo "Iniciando MikroBot Pro X na porta $PORT"
exec python3 service.py
