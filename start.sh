#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Starting Flask App Initialization ==="

# ------------------------------------------------------------------------------
# STEP 1: Check Required Tools
# ------------------------------------------------------------------------------
echo "[1/4] Checking required tools..."

if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "ERROR: Neither python3 nor python is installed or available in PATH!"
  echo "Please install Python 3.9+ before running ./start.sh"
  exit 1
fi

# Verify Python version (minimum Python 3.9)
PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]; }; then
  echo "ERROR: Python 3.9 or higher is required. Found Python ${PYTHON_MAJOR}.${PYTHON_MINOR}"
  exit 1
fi

# Verify the venv module works (on Ubuntu/Debian it is a separate package)
if ! $PYTHON_CMD -m venv --help >/dev/null 2>&1 || ! $PYTHON_CMD -c 'import ensurepip' >/dev/null 2>&1; then
  echo "ERROR: Python's venv module is missing."
  echo "On Ubuntu/Debian install it with: sudo apt install python3-venv"
  exit 1
fi

echo "Found $($PYTHON_CMD --version) at $(command -v $PYTHON_CMD)"

# ------------------------------------------------------------------------------
# STEP 2: Set Up Virtual Environment & Dependencies
# ------------------------------------------------------------------------------
echo "[2/4] Setting up Python virtual environment and installing dependencies..."

# Remove a half-created venv left behind by an earlier failed run
if [ -d "venv" ] && [ ! -f "venv/bin/activate" ] && [ ! -f "venv/Scripts/activate" ]; then
  echo "Found an incomplete ./venv, recreating it..."
  rm -rf venv
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment in ./venv..."
  if ! $PYTHON_CMD -m venv venv; then
    rm -rf venv
    echo "ERROR: Could not create the virtual environment."
    echo "On Ubuntu/Debian try: sudo apt install python3-venv"
    exit 1
  fi
fi

# Activate virtual environment (Windows Git Bash vs Linux/macOS)
if [ -f "venv/Scripts/activate" ]; then
  source venv/Scripts/activate
  VENV_PYTHON="venv/Scripts/python.exe"
else
  source venv/bin/activate
  VENV_PYTHON="venv/bin/python"
fi

# Upgrade pip via python module syntax to prevent Windows binary lock
"$VENV_PYTHON" -m pip install --quiet --upgrade pip

# Install project dependencies
if [ -f "requirements.txt" ]; then
  "$VENV_PYTHON" -m pip install --quiet -r requirements.txt
else
  echo "ERROR: requirements.txt not found in the root directory!"
  exit 1
fi

# ------------------------------------------------------------------------------
# STEP 3: Setup Application State / Environment
# ------------------------------------------------------------------------------
echo "[3/4] Preparing environment and application state..."

# Ensure .env exists if needed
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "Created default .env file from .env.example."
fi

# Run database setup or seed script if present
if [ -f "init_db.py" ]; then
  "$VENV_PYTHON" init_db.py
elif [ -f "schema.sql" ]; then
  "$VENV_PYTHON" -c "import sqlite3; conn = sqlite3.connect('app.db'); conn.executescript(open('schema.sql').read()); conn.close()"
fi

# ------------------------------------------------------------------------------
# STEP 4: Start Application
# ------------------------------------------------------------------------------
PORT=${PORT:-5000}
HOST=${HOST:-127.0.0.1}
URL="http://${HOST}:${PORT}"

export FLASK_APP=${FLASK_APP:-app.py}
export FLASK_DEBUG=${FLASK_DEBUG:-1}

echo "[4/4] Starting Flask server on ${URL}..."
echo "=================================================="
echo " App running at: ${URL}"
echo " Press Ctrl+C to stop the app."
echo "=================================================="

# Run flask server via active virtualenv python
exec "$VENV_PYTHON" -m flask run --host="$HOST" --port="$PORT"