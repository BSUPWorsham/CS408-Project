#!/bin/bash
# Repeatable update, run on each release: ./deploy/deploy.sh
set -e
cd "$(dirname "$0")/.."

git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python3 manage_db.py upgrade

sudo systemctl restart aplin-law
sleep 2
if sudo systemctl is-active --quiet aplin-law; then
    echo "Deployed. Health check:"
    curl -s http://127.0.0.1:8000/api/health || true
    echo
else
    echo "Service failed to start. Recent logs:"
    sudo journalctl -u aplin-law -n 30 --no-pager
    exit 1
fi
