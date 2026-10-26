# Aplin Law Website & Client Intake Portal

Website and client intake portal for Aplin Law, a nationwide Social Security disability firm based in Boise, Idaho.

**Stack:** Python 3, Flask, SQLite + SQLAlchemy, Jinja2, Bootstrap 5, ReportLab, Flask-Login, Flask-WTF (CSRF), Pytest, Gunicorn + systemd + Nginx on AWS EC2 (Ubuntu 22.04).

## Project layout

```
app/                 Flask application package
  __init__.py        create_app(), db, login manager, CSRF
  models.py          Users, Intakes, IntakeStatusHistory, ContactSubmissions
  public.py          Home, About, Practice Areas, How SS Works, Resources, Contact, /api/health
  auth.py            Staff /login and /logout
  admin.py           Protected /admin (dashboard built out in Checkpoint 4)
  templates/ static/ Jinja templates, CSS, images, generated PDFs
migrations/          Numbered SQL schema scripts
manage_db.py         Applies migrations (upgrade / status)
deploy/              Nginx config, systemd unit, EC2 setup and deploy scripts
tests/               Pytest suite
run.py               Development entry point
```

## Run locally

```bash
python -m venv venv
source venv/bin/activate          # Windows PowerShell: venv\Scripts\activate
pip install -r requirements.txt
export SECRET_KEY="long-random-string"
export ADMIN_EMAIL="admin@aplinlaw.com"
export ADMIN_PASSWORD="choose-a-password"
./configure.sh                    # creates the database and the first staff user
python run.py                     # http://127.0.0.1:5000
```

Windows without Git Bash: run `python manage_db.py upgrade` instead of `./configure.sh`, then create the admin user from Git Bash or WSL.

## Database migrations

```bash
python manage_db.py status        # show applied / pending
python manage_db.py upgrade       # apply pending
```

To change the schema, add `migrations/003_description.sql`, update `app/models.py` to match, and run `upgrade`. `tests/test_migrations.py` fails if the two drift apart.

## Tests

```bash
pytest
```

## Deploy to AWS EC2 (Ubuntu 22.04)

1. Launch a t2/t3.micro instance. Security group: inbound 22 (SSH) and 80 (HTTP).
2. `ssh -i your-key.pem ubuntu@<public-ip>`
3. `git clone https://github.com/BSUPWorsham/CS408-Project.git aplin-law-portal && cd aplin-law-portal`
4. `chmod +x install.sh configure.sh start.sh manage_db.py deploy/*.sh && ./install.sh`
5. Export secrets, then initialize:
   ```bash
   export SECRET_KEY="your-secure-random-secret-key"
   export ADMIN_EMAIL="admin@aplinlaw.com"
   export ADMIN_PASSWORD="your-secure-admin-password"
   source venv/bin/activate
   ./configure.sh
   ```
6. `./deploy/setup-ec2.sh` (installs Nginx, stores secrets in `/etc/aplin-law.env`, enables the systemd service).
7. Verify: `sudo systemctl status aplin-law`, visit `http://<public-ip>/`, then `sudo reboot` and confirm the site returns on its own.
8. Future updates: `./deploy/deploy.sh`.

Never commit `.pem` keys, `.env` files, or the database.

## Media

See `MEDIA_CREDITS.md` for sources and licenses.
