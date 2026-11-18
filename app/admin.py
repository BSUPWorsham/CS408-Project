"""Protected staff dashboard: filter intakes, change status (with history), delete records.

Every route here requires a signed-in staff member (Flask-Login). Signed-out
visitors are redirected to /login.

Filters on /admin are read from the query string, so a filtered view can be
bookmarked or shared between staff:

    /admin?status=New&age_category=60%2B&start=2026-11-01&end=2026-11-30
"""
import os
from datetime import date, datetime, time, timedelta

from flask import (Blueprint, abort, current_app, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.models import AGE_CATEGORIES, STATUSES, Intake, IntakeStatusHistory

admin = Blueprint("admin", __name__)


def parse_date(value):
    """Turn 'YYYY-MM-DD' into a date, or None if blank or invalid."""
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def read_filters(args):
    """Read and validate filter values from the query string.

    Returns (filters, errors). Unknown or malformed values are dropped and
    reported, so a bad link shows a message instead of an empty table.
    """
    filters = {"status": "", "age_category": "", "start": None, "end": None}
    errors = []

    status = args.get("status", "").strip()
    if status in STATUSES:
        filters["status"] = status
    elif status:
        errors.append(f'"{status}" is not a valid status, so that filter was ignored.')

    age = args.get("age_category", "").strip()
    if age in AGE_CATEGORIES:
        filters["age_category"] = age
    elif age:
        errors.append(f'"{age}" is not a valid age category, so that filter was ignored.')

    for key, label in (("start", "start date"), ("end", "end date")):
        raw = args.get(key, "").strip()
        filters[key] = parse_date(raw)
        if raw and filters[key] is None:
            errors.append(f"The {label} must look like 2026-11-30, so it was ignored.")

    if filters["start"] and filters["end"] and filters["start"] > filters["end"]:
        errors.append("The start date is after the end date, so the date range was ignored.")
        filters["start"] = filters["end"] = None

    return filters, errors


def filter_intakes(status="", age_category="", start=None, end=None):
    """Build the intake query for the given filters (newest first).

    `start` and `end` are dates and both are inclusive: end=2026-11-30 includes
    everything submitted on Nov 30.
    """
    query = Intake.query
    if status:
        query = query.filter(Intake.status == status)
    if age_category:
        query = query.filter(Intake.age_category == age_category)
    if start:
        query = query.filter(Intake.submitted_at >= datetime.combine(start, time.min))
    if end:
        query = query.filter(Intake.submitted_at < datetime.combine(end + timedelta(days=1), time.min))
    return query.order_by(Intake.submitted_at.desc(), Intake.intake_id.desc())


def get_intake_or_404(intake_id):
    record = db.session.get(Intake, intake_id)
    if record is None:
        abort(404)
    return record


@admin.route("/admin")
@login_required
def dashboard():
    filters, errors = read_filters(request.args)
    for message in errors:
        flash(message, "warning")

    intakes = filter_intakes(**filters).all()
    rows = db.session.query(Intake.status, func.count(Intake.intake_id)).group_by(Intake.status).all()
    counts = dict(rows)
    status_counts = [(s, counts.get(s, 0)) for s in STATUSES]
    is_filtered = any(filters.values())

    return render_template(
        "admin/dashboard.html", user=current_user, status_counts=status_counts,
        intakes=intakes, filters=filters, is_filtered=is_filtered,
        statuses=STATUSES, age_categories=AGE_CATEGORIES,
        total=sum(counts.values()),
    )


@admin.route("/admin/intakes/<int:intake_id>")
@login_required
def intake_detail(intake_id):
    record = get_intake_or_404(intake_id)
    has_pdf = bool(record.pdf_filename and os.path.exists(
        os.path.join(current_app.config["PDF_FOLDER"], record.pdf_filename)))
    history = sorted(record.history, key=lambda h: (h.changed_at, h.history_id), reverse=True)
    return render_template("admin/intake_detail.html", intake=record, history=history,
                           statuses=STATUSES, has_pdf=has_pdf)


@admin.route("/admin/intakes/<int:intake_id>/status", methods=["POST"])
@login_required
def update_status(intake_id):
    record = get_intake_or_404(intake_id)
    new_status = request.form.get("status", "").strip()

    if new_status not in STATUSES:
        flash("Choose a valid status.", "danger")
    elif new_status == record.status:
        flash(f"Status is already {new_status}; nothing changed.", "info")
    else:
        old_status = record.status or "New"
        db.session.add(IntakeStatusHistory(intake_id=record.intake_id,
                                           old_status=old_status, new_status=new_status))
        record.status = new_status
        db.session.commit()
        flash(f"Intake #{record.intake_id} moved from {old_status} to {new_status}.", "success")

    return redirect(url_for("admin.intake_detail", intake_id=record.intake_id))


@admin.route("/admin/intakes/<int:intake_id>/delete", methods=["POST"])
@login_required
def delete_intake(intake_id):
    record = get_intake_or_404(intake_id)
    if request.form.get("confirm") != "yes":
        flash("Check the confirmation box to delete this intake.", "warning")
        return redirect(url_for("admin.intake_detail", intake_id=record.intake_id))

    pdf_path = (os.path.join(current_app.config["PDF_FOLDER"], record.pdf_filename)
                if record.pdf_filename else None)
    name = record.client_name
    db.session.delete(record)  # its status history is removed too (cascade on the relationship)
    db.session.commit()

    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except OSError:
            current_app.logger.warning("Could not remove PDF %s", pdf_path)

    flash(f"Deleted intake #{intake_id} ({name}).", "success")
    return redirect(url_for("admin.dashboard"))


@admin.route("/admin/intakes/<int:intake_id>/pdf")
@login_required
def intake_pdf(intake_id):
    record = get_intake_or_404(intake_id)
    if not record.pdf_filename:
        abort(404)
    return send_from_directory(
        current_app.config["PDF_FOLDER"], record.pdf_filename,
        as_attachment=True, download_name=f"aplin-law-intake-{record.intake_id}.pdf",
        mimetype="application/pdf", max_age=0,
    )