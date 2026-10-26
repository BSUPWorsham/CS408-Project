"""Protected staff area. Full dashboard (filters, status updates, delete) arrives in Checkpoint 4."""
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.models import Intake, STATUSES

admin = Blueprint("admin", __name__)


@admin.route("/admin")
@login_required
def dashboard():
    rows = db.session.query(Intake.status, func.count(Intake.intake_id)).group_by(Intake.status).all()
    counts = dict(rows)
    status_counts = [(s, counts.get(s, 0)) for s in STATUSES]
    return render_template("admin/dashboard.html", user=current_user, status_counts=status_counts)
