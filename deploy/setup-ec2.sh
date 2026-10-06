#!/usr/bin/env bash

set -e

APP_NAME="my-app"
APP_DIR="/var/www/${APP_NAME}"
SYSTEMD_SERVICE="/etc/systemd/system/${APP_NAME}.service"
NGINX_CONF="/etc/nginx/sites-available/${APP_NAME}"

echo "[1/5] Installing system dependencies..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv nginx rsync

echo "[2/5] Creating app directory at ${APP_DIR}..."
mkdir -p "${APP_DIR}"
chown -R ubuntu:ubuntu "${APP_DIR}"

echo "[3/5] Setting up Systemd service..."
cp deploy/my-app.service "${SYSTEMD_SERVICE}"
systemctl daemon-reload
systemctl enable "${APP_NAME}"

echo "[4/5] Configuring Nginx..."
cp deploy/nginx-my-app.conf "${NGINX_CONF}"
ln -sf "${NGINX_CONF}" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx

echo "=== EC2 Setup Complete! Ready for deploy.sh ==="