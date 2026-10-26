#!/bin/bash
# One-time server provisioning. Run from anywhere AFTER install.sh and configure.sh,
# with SECRET_KEY, ADMIN_EMAIL and ADMIN_PASSWORD exported.
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_USER="$(id -un)"

if [ -z "$SECRET_KEY" ] || [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo "Error: export SECRET_KEY, ADMIN_EMAIL, and ADMIN_PASSWORD first."
    exit 1
fi

echo "=== Installing Nginx ==="
sudo apt-get update
sudo apt-get install -y nginx

echo "=== Writing Nginx site config (port 80 -> 127.0.0.1:8000) ==="
sudo cp "$APP_DIR/deploy/nginx-aplin-law.conf" /etc/nginx/sites-available/aplin-law
sudo ln -sf /etc/nginx/sites-available/aplin-law /etc/nginx/sites-enabled/aplin-law
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo "=== Writing /etc/aplin-law.env (mode 600) ==="
esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
sudo touch /etc/aplin-law.env
sudo chmod 600 /etc/aplin-law.env
{
    printf 'SECRET_KEY="%s"\n'     "$(esc "$SECRET_KEY")"
    printf 'ADMIN_EMAIL="%s"\n'    "$(esc "$ADMIN_EMAIL")"
    printf 'ADMIN_PASSWORD="%s"\n' "$(esc "$ADMIN_PASSWORD")"
} | sudo tee /etc/aplin-law.env > /dev/null

echo "=== Installing systemd service ==="
sed -e "s|/home/ubuntu/aplin-law-portal|$APP_DIR|g" -e "s|^User=.*|User=$RUN_USER|" \
    "$APP_DIR/deploy/aplin-law.service" | sudo tee /etc/systemd/system/aplin-law.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now aplin-law

echo "=== Done. Check: sudo systemctl status aplin-law ==="
