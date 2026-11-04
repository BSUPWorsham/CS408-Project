"""Checkpoint 4: multi-step intake, conditional branching, and database persistence."""
from app.models import Intake

VALID = {
    "client_name": "Pat Rivera",
    "client_email": "Pat@Example.com",
    "client_phone": "(208) 555-0123",
    "age_group": "50_59",
    "long_term": "yes",
    "disability_details": "Back injury from 30 years of warehouse work; can't lift over 10 lbs.",
    "tried_accommodations": "yes",
    "case_summary": "Forklift operator since 1994. Stopped working in March after surgery.",
}


def post_step(client, step, action="next", **overrides):
    data = {**VALID, **overrides, "step": str(step), "action": action}
    return client.post("/intake", data=data)


def test_intake_first_step_loads(client):
    resp = client.get("/intake")
    assert resp.status_code == 200
    assert b"Step 1 of 5" in resp.data
    assert b'name="client_name"' in resp.data


def test_each_step_advances_to_the_next(client):
    for step, title in [(1, b"Step 2 of 5"), (2, b"Step 3 of 5"), (3, b"Step 4 of 5"), (4, b"Step 5 of 5")]:
        resp = post_step(client, step)
        assert resp.status_code == 200, step
        assert title in resp.data, step


def test_valid_intake_submission(client, app):
    resp = post_step(client, 5)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/intake/submitted")

    with app.app_context():
        saved = Intake.query.one()
        assert saved.client_name == "Pat Rivera"
        assert saved.client_email == "pat@example.com"
        assert saved.age_category == "50-59"
        assert saved.tried_accommodations is True
        assert saved.status == "New"

    confirmation = client.get("/intake/submitted")
    assert confirmation.status_code == 200
    assert f"#{saved.intake_id}".encode() in confirmation.data


def test_child_applicant_saved_with_child_category(client, app):
    post_step(client, 5, age_group="child", tried_accommodations="no")
    with app.app_context():
        saved = Intake.query.one()
        assert saved.age_category == "Child Disability"
        assert saved.tried_accommodations is False


def test_conditional_branching_out_of_scope(client, app):
    resp = post_step(client, 2, age_group="under_50", long_term="no")
    assert resp.status_code == 302
    assert "/intake/not-a-fit" in resp.headers["Location"]

    page = client.get(resp.headers["Location"])
    assert page.status_code == 200
    assert b"Legal aid" in page.data  # external resource recommendations
    with app.app_context():
        assert Intake.query.count() == 0


def test_under_50_is_out_of_scope_even_with_long_term_condition(client):
    resp = post_step(client, 2, age_group="under_50", long_term="yes")
    assert "reason=age" in resp.headers["Location"]


def test_short_term_condition_is_out_of_scope(client):
    resp = post_step(client, 2, age_group="60_plus", long_term="no")
    assert "reason=duration" in resp.headers["Location"]


def test_unsure_duration_continues(client):
    resp = post_step(client, 2, long_term="unsure")
    assert resp.status_code == 200
    assert b"Step 3 of 5" in resp.data


def test_out_of_scope_answers_cannot_be_submitted_at_the_end(client, app):
    resp = post_step(client, 5, age_group="under_50")
    assert resp.status_code == 302
    assert "/intake/not-a-fit" in resp.headers["Location"]
    with app.app_context():
        assert Intake.query.count() == 0


def test_form_validation_missing_fields(client, app):
    resp = post_step(client, 1, client_name="", client_email="not-an-email", client_phone="123")
    assert resp.status_code == 400
    assert b"Step 1 of 5" in resp.data
    assert b"Enter your full name." in resp.data
    assert b"Enter an email address like name@example.com." in resp.data
    assert b"Enter a phone number with area code" in resp.data
    with app.app_context():
        assert Intake.query.count() == 0


def test_skipped_step_is_caught_on_submit(client, app):
    # Jumping straight to the last step with an earlier step blank sends you back to it.
    resp = post_step(client, 5, disability_details="")
    assert resp.status_code == 400
    assert b"Step 3 of 5" in resp.data
    assert b"Describe the injury or condition." in resp.data
    with app.app_context():
        assert Intake.query.count() == 0


def test_back_button_keeps_answers_without_validating(client):
    resp = post_step(client, 3, action="back", disability_details="")
    assert resp.status_code == 200
    assert b"Step 2 of 5" in resp.data
    assert b'value="Pat Rivera"' in resp.data  # earlier answers ride along


def test_review_page_shows_answers_and_edit_jumps_back(client):
    review = post_step(client, 4)
    assert b"Step 5 of 5" in review.data
    assert b"Forklift operator since 1994" in review.data

    edit = post_step(client, 5, action="edit-1")
    assert b"Step 1 of 5" in edit.data
    assert b'value="pat@example.com"' in edit.data.lower()


def test_confirmation_page_requires_a_submission(client):
    assert client.get("/intake/submitted").status_code == 404