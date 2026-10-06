#!/usr/bin/env bash
# Run on your laptop:  ./deploy/deploy.sh -h <PUBLIC-IP> -i <KEY-PATH>
set -euo pipefail

APP_NAME="my-app"
APP_DIR="/var/www/${APP_NAME}"
REMOTE_USER="ubuntu"

usage() {
  echo "Usage: $0 -h <PUBLIC-IP> -i <KEY-PATH>"
  exit 1
}

HOST=""
KEY_PATH=""
while getopts "h:i:" opt; do
  case $opt in
    h) HOST="$OPTARG" ;;
    i) KEY_PATH="$OPTARG" ;;
    *) usage ;;
  esac
done

if [ -z "$HOST" ] || [ -z "$KEY_PATH" ]; then
  echo "ERROR: Missing required arguments."
  usage
fi
if [ ! -f "$KEY_PATH" ]; then
  echo "ERROR: Key file not found: $KEY_PATH"
  exit 1
fi

# Always work from the repository root
cd "$(dirname "$0")/.."

SSH_OPTS=(-i "$KEY_PATH" -o StrictHostKeyChecking=accept-new)
TARGET="${REMOTE_USER}@${HOST}"

echo "=== Deploying to ${HOST} ==="

echo "[1/4] Running local tests..."
if [ -d tests ]; then
  if [ -f venv/bin/python ]; then PY="venv/bin/python"
  elif [ -f venv/Scripts/python.exe ]; then PY="venv/Scripts/python.exe"
  elif command -v python3 >/dev/null 2>&1; then PY="python3"
  else PY="python"; fi
  "$PY" -m pytest -q
else
  echo "No tests/ folder found, skipping tests."
fi

echo "[2/4] Syncing files to server..."
ssh "${SSH_OPTS[@]}" "$TARGET" "mkdir -p ${APP_DIR}"
if command -v rsync >/dev/null 2>&1; then
  rsync -az \
    --exclude '.git/' --exclude '.idea/' --exclude 'venv/' --exclude '__pycache__/' \
    --exclude 'tests/' --exclude '*.pem' --exclude '.env' \
    -e "ssh -i \"$KEY_PATH\" -o StrictHostKeyChecking=accept-new" \
    ./ "${TARGET}:${APP_DIR}/"
else
  echo "(rsync not found, falling back to scp)"
  FILES=()
  for f in app.py requirements.txt deploy templates static; do
    [ -e "$f" ] && FILES+=("$f")
  done
  scp "${SSH_OPTS[@]}" -r "${FILES[@]}" "${TARGET}:${APP_DIR}/"
fi

echo "[3/4] Installing dependencies and restarting service..."
ssh "${SSH_OPTS[@]}" "$TARGET" "cd ${APP_DIR} \
  && { [ -x venv/bin/python ] || python3 -m venv venv; } \
  && ./venv/bin/pip install -q -r requirements.txt \
  && sudo systemctl restart ${APP_NAME}"

echo "[4/4] Checking http://${HOST}/api/health ..."
for i in $(seq 1 10); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${HOST}/api/health" || true)
  if [ "$STATUS" = "200" ]; then
    echo "SUCCESS: deployed and live at http://${HOST}/ (health check HTTP 200)"
    exit 0
  fi
  sleep 2
done

echo "ERROR: health check failed (last status: ${STATUS:-none})"
echo "Debug with: ssh -i \"$KEY_PATH\" ${TARGET} 'sudo journalctl -u ${APP_NAME} -n 30 --no-pager'"
exit 1