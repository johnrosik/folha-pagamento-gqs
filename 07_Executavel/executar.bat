@echo off
rem Financy: instala as dependências (primeira vez) e abre a interface em http://localhost:8080
cd /d "%~dp0..\05_Codigo_Fonte"
if not exist ".venv" (
    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt
)
.venv\Scripts\python interface.py
