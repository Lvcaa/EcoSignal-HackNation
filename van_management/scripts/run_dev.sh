#!/usr/bin/env bash
# Quick dev runner — starts uvicorn with reload
set -e
cd "$(dirname "$0")/.."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
