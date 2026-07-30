#!/usr/bin/env bash
# ============================================================
#  ISPL Payroll — start the app (macOS / Linux).
#    chmod +x run.sh   (once)   then:   ./run.sh
# ============================================================
cd "$(dirname "$0")" || exit 1

if [ ! -f erp.config.sh ]; then
  cp erp.config.example.sh erp.config.sh
  echo "First-time setup: created erp.config.sh."
  echo "Edit it with your database details, then run ./run.sh again."
  exit 1
fi

# shellcheck disable=SC1091
source erp.config.sh

echo "Installing dependencies (first run only)..."
python3 -m pip install -r requirements.txt

echo "Setting up the database (safe to repeat)..."
python3 init_db.py || { echo "Setup failed — check erp.config.sh"; exit 1; }

echo
echo "============================================================"
echo " ISPL Payroll is starting."
echo " Open in your browser:  http://127.0.0.1:8000"
echo " (Keep this terminal open. Ctrl+C to stop.)"
echo "============================================================"
python3 app.py
