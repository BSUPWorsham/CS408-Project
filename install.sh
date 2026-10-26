#!/bin/bash
# One-time: install system packages and create the Python virtual environment.
set -e

echo "=== Updating System Packages ==="
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv sqlite3

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "=== install.sh finished ==="
