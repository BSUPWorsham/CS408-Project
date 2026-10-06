#!/usr/bin/env bash

# 1. Parse command line flags
while getopts "h:i:" opt; do
  case $opt in
    h) HOST="$OPTARG" ;;
    i) KEY_PATH="$OPTARG" ;;
    *) exit 1 ;;
  esac
done

# 2. Check if required arguments were provided
if [ -z "$HOST" ] || [ -z "$KEY_PATH" ]; then
  echo "ERROR: Missing required arguments."
  echo "Usage: $0 -h <PUBLIC-IP> -i <KEY-PATH>"
  exit 1
fi

echo "=== [Task 3] Deploying to ${HOST} ==="

# 1. Run local test suite
echo "[1/4] Running local tests..."
if [ -d "venv" ]; then
    if [ -f "venv/Scripts/activate" ]; then source venv/Scripts/activate; else source venv/bin/activate; fi
    pytest
else
    python3 -m pytest
fi

echo "[2/4] Syncing files to server..."
scp -i "$KEY_PATH" -r app.py requirements.txt deploy ubuntu@"$HOST":/var/www/my-app/

# [3/4] Installing remote dependencies & restarting service...
echo "[3/4] Installing remote dependencies & restarting service..."
ssh -i "$KEY_PATH" ubuntu@"$HOST" "cd /var/www/my-app && ./venv/bin/pip install -r requirements.txt && sudo systemctl restart my-app && sudo systemctl restart nginx"

# 4. Verify deployment via Health Check
echo "[4/4] Verifying health check endpoint..."
sleep 3
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST}/")

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "SUCCESS: App successfully deployed and live at http://${HOST}/ (HTTP 200)"
else
    echo "ERROR: Health check failed with status code ${HTTP_STATUS}"
    exit 1
fi