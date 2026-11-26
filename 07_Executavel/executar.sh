#!/usr/bin/env sh
# Financy: instala as dependências (primeira vez) e abre a interface em http://localhost:8080
cd "$(dirname "$0")/../05_Codigo_Fonte" || exit 1
if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python interface.py
