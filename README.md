# Aplin Law Website & Client Intake Portal (CS408)

Flask site for Aplin Law, a Social Security disability firm in Boise, Idaho.

## Run locally
```bash
./start.sh            # creates venv, installs requirements, serves http://127.0.0.1:5000
pip install pytest && python -m pytest -q
```

## Layout
- `app.py` — routes and page content data (firm info, claim stages, resource links)
- `templates/` — Jinja2 pages extending `base.html` (shared nav and footer)
- `static/css/site.css` — styles layered on Bootstrap 5 (CDN)
- `static/img/` — logo, favicon, placeholder graphics
- `tests/` — pytest suite (run by `deploy/deploy.sh` before each release)
- `MEDIA_CREDITS.md` — source and license for every image, icon, and font

## Checkpoint 2 pages
| Route | Page |
|-------|------|
| `/` | Home |
| `/about` | About Us |
| `/practice-areas` | Practice Areas & Stages |
| `/how-social-security-works` | How Social Security Works |
| `/resources` | Resource Center |
| `/contact` | Contact Us (validated form; saved to the database in Checkpoint 3) |
| `/intake`, `/login` | Placeholders until Checkpoints 3–4 |
