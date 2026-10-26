#!/bin/bash
# Production start: Gunicorn on 127.0.0.1:8000 (Nginx proxies port 80 here).
cd "$(dirname "$0")"
source venv/bin/activate
exec gunicorn --workers 2 --bind 127.0.0.1:8000 run:app
