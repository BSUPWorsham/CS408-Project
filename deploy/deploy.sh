#!/usr/bin/env bash

set -e

# Default variables
HOST=""
KEY=""
USER="ubuntu"
APP_NAME="my-app"
APP_DIR="/var/www/${APP_NAME}"

# Parse CLI flags (-h <HOST> -i <KEY>)
while getopts "h:i:" opt; do
  case ${opt} in
    h ) HOST=$OPTARG ;;
    i ) KEY=$OPTARG ;;
    \? ) echo "Usage: ./deploy/deploy.sh -h <PUBLIC-IP> -i <KEY-PATH>"; exit 1 ;;
  esac
done

if [ -z "$HOST" ] || [ -z "$KEY" ]; then
    echo "ERROR: Missing required arguments."
    echo "Usage: ./deploy/deploy.sh -h <PUBLIC-IP> -i <KEY-PATH>"
    exit 1
fi

echo "=== [Task 3] Deploying to ${HOST} ==="

# 1. Run local test suite
echo "[1/4] Running local tests..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pytest
else
    python3 -m pytest
fi

# 2. Sync project code using rsync
echo "[2/4] Syncing files to server..."
rsync -avz -e "ssh -i ${KEY} -o StrictHostKeyChecking=no" \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude '*.db' \
    --exclude '.pytest_cache' \
    ./ "${USER}@${HOST}:${APP_DIR}/"

# 3. Remote build & restart application
echo "[3/4] Installing remote dependencies & restarting service..."
ssh -i "${KEY}" -o StrictHostKeyChecking=no "${USER}@${HOST}" << EOF
    set -e
    cd ${APP_DIR}
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    ./venv/bin/pip install --quiet -r requirements.txt
    sudo systemctl restart ${APP_NAME}
EOF

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