import pytest
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import Intake, IntakeStatusHistory, User


def make_intake(**overrides):
    data = dict(
        client_name="Pat Doe", client_email="pat@example.com", client_phone="208-555-0101",
        age_category="50-59", disability_details="Back injury", tried_accommodations=True,
        case_summary="Warehouse worker for 25 years.",
    )
    data.update(overrides)
    return Intake(**data)


def test_intake_defaults(app):
    intake = make_intake()
    db.session.add(intake)
    db.session.commit()
    assert intake.status == "New"
    assert intake.submitted_at is not None
    assert intake.pdf_filename is None


def test_intake_requires_fields(app):
    db.session.add(Intake(client_name="Only a name"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_status_history_relationship(app):
    intake = make_intake()
    db.session.add(intake)
    db.session.commit()
    db.session.add(IntakeStatusHistory(intake_id=intake.intake_id, old_status="New", new_status="In Review"))
    db.session.commit()
    assert [(h.old_status, h.new_status) for h in intake.history] == [("New", "In Review")]


def test_deleting_intake_removes_its_history(app):
    intake = make_intake()
    db.session.add(intake)
    db.session.commit()
    db.session.add(IntakeStatusHistory(intake_id=intake.intake_id, old_status="New", new_status="Archived"))
    db.session.commit()
    db.session.delete(intake)
    db.session.commit()
    assert IntakeStatusHistory.query.count() == 0


def test_user_email_must_be_unique(app):
    for _ in range(2):
        u = User(email="dup@aplinlaw.com", full_name="Dup")
        u.set_password("pw")
        db.session.add(u)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
