"""Checkpoint 5: ReportLab PDF generation on intake submission."""
import os

from app import db
from app.models import Intake
from app.pdf import generate_intake_pdf

VALID = {
    "client_name": "Pat Rivera",
    "client_email": "pat@example.com",
    "client_phone": "(208) 555-0123",
    "age_group": "60_plus",
    "long_term": "yes",
    "disability_details": "Torn rotator cuff and two knee surgeries after 28 years of framing.",
    "tried_accommodations": "no",
    "case_summary": "Carpenter since 1996. Denied at the initial application in August.",
    "step": "5",
    "action": "next",
}


def submit(client, **overrides):
    return client.post("/intake", data={**VALID, **overrides})


def pdf_path(app, record):
    return os.path.join(app.config["PDF_FOLDER"], record.pdf_filename)


def test_pdf_creation_on_submission(client, app):
    submit(client)
    record = Intake.query.one()

    assert record.pdf_filename
    assert record.pdf_filename.startswith(f"intake_{record.intake_id}_")
    assert os.path.isfile(pdf_path(app, record))
    with open(pdf_path(app, record), "rb") as f:
        assert f.read(5) == b"%PDF-"


def test_pdf_content_matches_intake(client, app):
    submit(client)
    record = Intake.query.one()
    with open(pdf_path(app, record), "rb") as f:
        content = f.read()

    for expected in [b"Pat Rivera", b"pat@example.com", b"555-0123", b"60+",
                     f"Reference #{record.intake_id}".encode(), b"Carpenter since 1996"]:
        assert expected in content, expected


def test_pdf_handles_special_characters(app):
    record = Intake(
        client_name="Ana <O'Brien> & Sons", client_email="ana@example.com", client_phone="2085550199",
        age_category="Child Disability", disability_details="Line one\nLine two < 3 > 1",
        tried_accommodations=True, case_summary="Uses \"quotes\" & ampersands.",
    )
    db.session.add(record)
    db.session.commit()

    filename = generate_intake_pdf(record, app.config["PDF_FOLDER"])
    assert os.path.getsize(os.path.join(app.config["PDF_FOLDER"], filename)) > 1000


def test_pdf_file_names_are_not_guessable(client, app):
    submit(client)
    submit(client, client_name="Second Client")
    first, second = Intake.query.order_by(Intake.intake_id).all()
    assert first.pdf_filename != second.pdf_filename
    assert len(first.pdf_filename) > len(f"intake_{first.intake_id}_.pdf") + 10


def test_confirmation_page_has_download_button(client):
    submit(client)
    page = client.get("/intake/submitted")
    assert page.status_code == 200
    assert b"Download PDF summary" in page.data
    assert b'href="/intake/submitted/pdf"' in page.data


def test_pdf_download(client):
    submit(client)
    resp = client.get("/intake/submitted/pdf")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert "attachment" in resp.headers["Content-Disposition"]
    assert resp.data.startswith(b"%PDF-")


def test_pdf_download_requires_your_own_submission(client, app):
    submit(client)
    other_visitor = app.test_client()  # new browser, no session
    assert other_visitor.get("/intake/submitted/pdf").status_code == 404


def test_out_of_scope_intake_creates_no_pdf(client, app):
    submit(client, age_group="under_50")
    assert Intake.query.count() == 0
    folder = app.config["PDF_FOLDER"]
    assert not os.path.isdir(folder) or os.listdir(folder) == []


def test_intake_still_saved_if_pdf_fails(client, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("ReportLab exploded")
    monkeypatch.setattr("app.intake.generate_intake_pdf", broken)

    resp = submit(client)
    assert resp.status_code == 302
    record = Intake.query.one()
    assert record.pdf_filename is None

    page = client.get("/intake/submitted")
    assert b"Download PDF summary" not in page.data
    assert b"isn&#39;t ready" in page.data or b"isn't ready" in page.data