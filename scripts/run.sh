#!/usr/bin/env bash
set -e
echo "[QuantWeb] Starting local dev server..."
python3 -m uvicorn quant_web.main:app --host 0.0.0.0 --port 8000 --reload
