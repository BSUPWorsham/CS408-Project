#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu EC2 server. Run ON THE SERVER:
#   sudo bash deploy/setup-ec2.sh
set -euo pipefail

APP_NAME="my-app"
APP_USER="ubuntu"
APP_DIR="/var/www/${APP_NAME}"
SYSTEMD_SERVICE="/etc/systemd/system/${APP_NAME}.service"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run this with sudo: sudo bash deploy/setup-ec2.sh"
  exit 1
fi

echo "[1/6] Installing system dependencies..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv nginx rsync

echo "[2/6] Creating app directory at ${APP_DIR}..."
mkdir -p "${APP_DIR}"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "[3/6] Creating Python virtual environment..."
if [ ! -x "${APP_DIR}/venv/bin/python" ]; then
  rm -rf "${APP_DIR}/venv"
  sudo -u "${APP_USER}" python3 -m venv "${APP_DIR}/venv"
fi

echo "[4/6] Installing systemd service..."
cp "${SCRIPT_DIR}/${APP_NAME}.service" "${SYSTEMD_SERVICE}"
systemctl daemon-reload
systemctl enable "${APP_NAME}"

echo "[5/6] Configuring nginx..."
cp "${SCRIPT_DIR}/nginx-${APP_NAME}.conf" "${NGINX_CONF}"
ln -sf "${NGINX_CONF}" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

echo "[6/6] Restarting nginx..."
systemctl restart nginx
systemctl enable nginx

echo "=== EC2 setup complete! Now run ./deploy/deploy.sh from your laptop ==="