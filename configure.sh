#!/bin/bash
set -e
if [ -z "$SECRET_KEY" ] || [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo "Error: SECRET_KEY, ADMIN_EMAIL, and ADMIN_PASSWORD must be set in your environment."
    exit 1
fi
mkdir -p app/static/uploads/pdfs
mkdir -p app/instance

# Create / update the database schema from migrations/*.sql
python3 manage_db.py upgrade

# Seed the first staff user (skipped if it already exists)
python3 -c "
import os
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    admin_email = os.environ['ADMIN_EMAIL'].strip().lower()
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, full_name='System Administrator')
        admin.set_password(os.environ['ADMIN_PASSWORD'])
        db.session.add(admin)
        db.session.commit()
        print('Admin user initialized successfully.')
    else:
        print('Admin user already exists.')
"
