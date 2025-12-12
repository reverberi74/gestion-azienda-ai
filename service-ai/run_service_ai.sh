#!/usr/bin/env bash 
cd "$(dirname "$0")"
source .venv/Scripts/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8001