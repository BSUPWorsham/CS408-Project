"""Checkpoint 6: protected dashboard, filters, status history, and deletion."""
import os
from datetime import date, datetime

import pytest

from app import db
from app.admin import filter_intakes, read_filters
from app.models import Intake, IntakeStatusHistory


def make_intake(name, status="New", age="50-59", submitted=datetime(2026, 11, 10, 15, 0), pdf=None):
    record = Intake(
        client_name=name, client_email=f"{name.split()[0].lower()}@example.com",
        client_phone="2085550100", age_category=age,
        disability_details="Back injury.", tried_accommodations=True,
        case_summary="Warehouse worker for 25 years.", status=status,
        submitted_at=submitted, pdf_filename=pdf,
    )
    db.session.add(record)
    db.session.commit()
    return record


@pytest.fixture
def sample_intakes(app):
    return {
        "ann": make_intake("Ann New", "New", "50-59", datetime(2026, 11, 1, 9, 0)),
        "bob": make_intake("Bob Review", "In Review", "60+", datetime(2026, 11, 15, 23, 30)),
        "cal": make_intake("Cal Child", "New", "Child Disability", datetime(2026, 11, 30, 18, 0)),
        "dee": make_intake("Dee Archived", "Archived", "60+", datetime(2026, 10, 20, 12, 0)),
    }


def names(query):
    return {i.client_name for i in query.all()}


# --- Access control ---------------------------------------------------------

@pytest.mark.parametrize("method, path", [
    ("get", "/admin"),
    ("get", "/admin/intakes/1"),
    ("post", "/admin/intakes/1/status"),
    ("post", "/admin/intakes/1/delete"),
    ("get", "/admin/intakes/1/pdf"),
])
def test_admin_routes_require_login(client, sample_intakes, method, path):
    resp = getattr(client, method)(path, data={"status": "Archived", "confirm": "yes"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert db.session.get(Intake, 1).status == "New"  # nothing changed


# --- Conditional data retrieval ----------------------------------------------

def test_conditional_filter_by_status(app, sample_intakes):
    assert names(filter_intakes(status="New")) == {"Ann New", "Cal Child"}
    assert names(filter_intakes(status="In Review")) == {"Bob Review"}


def test_conditional_filter_by_age_category(app, sample_intakes):
    assert names(filter_intakes(age_category="60+")) == {"Bob Review", "Dee Archived"}
    assert names(filter_intakes(age_category="Child Disability")) == {"Cal Child"}


def test_conditional_filter_by_date_range(app, sample_intakes):
    nov = filter_intakes(start=date(2026, 11, 1), end=date(2026, 11, 30))
    assert names(nov) == {"Ann New", "Bob Review", "Cal Child"}  # both ends inclusive

    mid = filter_intakes(start=date(2026, 11, 2), end=date(2026, 11, 15))
    assert names(mid) == {"Bob Review"}  # 23:30 on the end date still counts


def test_filters_combine(app, sample_intakes):
    query = filter_intakes(status="New", age_category="50-59",
                           start=date(2026, 11, 1), end=date(2026, 11, 30))
    assert names(query) == {"Ann New"}


def test_results_are_newest_first(app, sample_intakes):
    order = [i.client_name for i in filter_intakes().all()]
    assert order == ["Cal Child", "Bob Review", "Ann New", "Dee Archived"]


def test_dashboard_filters_from_query_string(client, login, sample_intakes):
    login()
    page = client.get("/admin?status=New&age_category=Child+Disability")
    assert page.status_code == 200
    assert b"Cal Child" in page.data
    assert b"Ann New" not in page.data
    assert b"Showing 1 of 4 intakes (filtered)" in page.data


def test_dashboard_lists_everything_without_filters(client, login, sample_intakes):
    login()
    page = client.get("/admin")
    for name in (b"Ann New", b"Bob Review", b"Cal Child", b"Dee Archived"):
        assert name in page.data


def test_invalid_filters_are_ignored_with_a_message(app):
    from werkzeug.datastructures import MultiDict
    filters, errors = read_filters(MultiDict({
        "status": "Bogus", "age_category": "40-49", "start": "not-a-date", "end": "2026-11-01",
    }))
    assert filters == {"status": "", "age_category": "", "start": None, "end": date(2026, 11, 1)}
    assert len(errors) == 3


def test_start_after_end_drops_date_range(app):
    from werkzeug.datastructures import MultiDict
    filters, errors = read_filters(MultiDict({"start": "2026-12-01", "end": "2026-11-01"}))
    assert filters["start"] is None and filters["end"] is None
    assert errors


# --- Detail view ---------------------------------------------------------------

def test_intake_detail_page(client, login, sample_intakes):
    login()
    page = client.get(f"/admin/intakes/{sample_intakes['bob'].intake_id}")
    assert page.status_code == 200
    assert b"Bob Review" in page.data
    assert b"Warehouse worker for 25 years." in page.data
    assert b"No changes yet" in page.data


def test_missing_intake_returns_404(client, login):
    login()
    assert client.get("/admin/intakes/999").status_code == 404


# --- Status management with history ------------------------------------------

def test_update_intake_status(client, login, sample_intakes):
    login()
    ann = sample_intakes["ann"]
    resp = client.post(f"/admin/intakes/{ann.intake_id}/status", data={"status": "In Review"})
    assert resp.status_code == 302

    assert db.session.get(Intake, ann.intake_id).status == "In Review"
    history = IntakeStatusHistory.query.filter_by(intake_id=ann.intake_id).all()
    assert [(h.old_status, h.new_status) for h in history] == [("New", "In Review")]
    assert history[0].changed_at is not None

    client.post(f"/admin/intakes/{ann.intake_id}/status", data={"status": "Contacted"})
    page = client.get(f"/admin/intakes/{ann.intake_id}")
    assert IntakeStatusHistory.query.filter_by(intake_id=ann.intake_id).count() == 2
    assert b"In Review &rarr; Contacted" in page.data


def test_same_status_adds_no_history(client, login, sample_intakes):
    login()
    ann = sample_intakes["ann"]
    client.post(f"/admin/intakes/{ann.intake_id}/status", data={"status": "New"})
    assert IntakeStatusHistory.query.count() == 0


def test_invalid_status_is_rejected(client, login, sample_intakes):
    login()
    ann = sample_intakes["ann"]
    client.post(f"/admin/intakes/{ann.intake_id}/status", data={"status": "Closed"})
    assert db.session.get(Intake, ann.intake_id).status == "New"
    assert IntakeStatusHistory.query.count() == 0


# --- Deletion ------------------------------------------------------------------

def test_delete_intake_record(client, login, app, sample_intakes):
    login()
    folder = app.config["PDF_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    pdf_name = "intake_test_abc.pdf"
    with open(os.path.join(folder, pdf_name), "wb") as f:
        f.write(b"%PDF-1.4 test")

    dup = make_intake("Duplicate Test", pdf=pdf_name)
    client.post(f"/admin/intakes/{dup.intake_id}/status", data={"status": "Archived"})
    dup_id = dup.intake_id

    resp = client.post(f"/admin/intakes/{dup_id}/delete", data={"confirm": "yes"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/admin")

    db.session.expire_all()
    assert db.session.get(Intake, dup_id) is None
    assert IntakeStatusHistory.query.filter_by(intake_id=dup_id).count() == 0
    assert not os.path.exists(os.path.join(folder, pdf_name))
    assert Intake.query.count() == 4  # the other records are untouched


def test_delete_requires_confirmation(client, login, sample_intakes):
    login()
    ann = sample_intakes["ann"]
    client.post(f"/admin/intakes/{ann.intake_id}/delete", data={})
    assert db.session.get(Intake, ann.intake_id) is not None


def test_delete_requires_post(client, login, sample_intakes):
    login()
    assert client.get(f"/admin/intakes/{sample_intakes['ann'].intake_id}/delete").status_code == 405


# --- PDF download --------------------------------------------------------------

def test_staff_can_download_intake_pdf(client, login, app):
    login()
    folder = app.config["PDF_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "intake_x.pdf"), "wb") as f:
        f.write(b"%PDF-1.4 test")
    record = make_intake("Pdf Person", pdf="intake_x.pdf")

    resp = client.get(f"/admin/intakes/{record.intake_id}/pdf")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data.startswith(b"%PDF")