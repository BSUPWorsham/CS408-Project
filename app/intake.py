"""Multi-step client intake with conditional branching.

The form runs over five server-rendered steps with no JavaScript required:

    1. Contact      name, email, phone
    2. Situation    age group, whether the condition will last 12+ months
    3. Condition    disability details, attempted accommodations
    4. Your story   case summary
    5. Review       confirm and submit

Answers from earlier steps travel forward as hidden fields, and every request
re-validates all steps up to the current one, so a skipped or tampered step is
caught. Nothing is saved until the final submit.

Branching happens right after step 2. Two answers end the intake and send the
visitor to the not-a-fit page with outside resources instead:

    * age group "Under 50"   (the firm serves workers 50+ and families of
                              disabled children)
    * condition will NOT last 12 months  (Social Security's duration rule)
"""
import re

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app import db
from app.models import Intake

intake = Blueprint("intake", __name__)

STEPS = ["Contact", "Situation", "Condition", "Your story", "Review"]
LAST_STEP = len(STEPS)

# Radio value -> (label shown to the visitor, Intakes.age_category stored, or None if out of scope)
AGE_GROUPS = {
    "under_50": ("I am under 50", None),
    "50_59": ("I am 50 to 59", "50-59"),
    "60_plus": ("I am 60 or older", "60+"),
    "child": ("I am applying for my child or adult child", "Child Disability"),
}
DURATION_CHOICES = {
    "yes": "Yes",
    "no": "No",
    "unsure": "I'm not sure yet",
}
YES_NO = {"yes": "Yes", "no": "No"}

# Every field the form carries, in the order the steps collect them.
FIELDS = [
    "client_name", "client_email", "client_phone",
    "age_group", "long_term",
    "disability_details", "tried_accommodations",
    "case_summary",
]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEXT_LIMIT = 5000

OUT_OF_SCOPE_REASONS = {
    "age": "We focus on workers age 50 and older and on families of disabled children, "
           "so we are not the right firm for this claim.",
    "duration": "Social Security disability only covers conditions expected to last at least "
                "12 months, so this claim is unlikely to qualify right now.",
}


def clean(form):
    """Pull every intake field from a submitted form, trimmed."""
    return {name: form.get(name, "").strip() for name in FIELDS}


def validate_step(step, data):
    """Return {field: message} for problems in one step's answers."""
    errors = {}
    if step == 1:
        if not data["client_name"]:
            errors["client_name"] = "Enter your full name."
        elif len(data["client_name"]) > 100:
            errors["client_name"] = "Keep your name under 100 characters."
        if not EMAIL_RE.match(data["client_email"]) or len(data["client_email"]) > 120:
            errors["client_email"] = "Enter an email address like name@example.com."
        digits = re.sub(r"\D", "", data["client_phone"])
        if not 10 <= len(digits) <= 15 or len(data["client_phone"]) > 20:
            errors["client_phone"] = "Enter a phone number with area code, like (208) 555-0100."
    elif step == 2:
        if data["age_group"] not in AGE_GROUPS:
            errors["age_group"] = "Choose the option that describes you."
        if data["long_term"] not in DURATION_CHOICES:
            errors["long_term"] = "Choose yes, no, or not sure."
    elif step == 3:
        if not data["disability_details"]:
            errors["disability_details"] = "Describe the injury or condition."
        elif len(data["disability_details"]) > TEXT_LIMIT:
            errors["disability_details"] = f"Keep this under {TEXT_LIMIT} characters."
        if data["tried_accommodations"] not in YES_NO:
            errors["tried_accommodations"] = "Choose yes or no."
    elif step == 4:
        if not data["case_summary"]:
            errors["case_summary"] = "Tell us a little about your work history and situation."
        elif len(data["case_summary"]) > TEXT_LIMIT:
            errors["case_summary"] = f"Keep this under {TEXT_LIMIT} characters."
    return errors


def first_invalid_step(data, up_to):
    """Re-check steps 1..up_to; return (step, errors) for the first bad one, else (None, {})."""
    for step in range(1, min(up_to, LAST_STEP - 1) + 1):
        errors = validate_step(step, data)
        if errors:
            return step, errors
    return None, {}


def out_of_scope_reason(data):
    """Branching rule: return a reason code if the answers fall outside the firm's scope."""
    if data["age_group"] == "under_50":
        return "age"
    if data["long_term"] == "no":
        return "duration"
    return None


def build_intake(data):
    """Turn validated answers into an Intakes row."""
    return Intake(
        client_name=data["client_name"],
        client_email=data["client_email"].lower(),
        client_phone=data["client_phone"],
        age_category=AGE_GROUPS[data["age_group"]][1],
        disability_details=data["disability_details"],
        tried_accommodations=data["tried_accommodations"] == "yes",
        case_summary=data["case_summary"],
        status="New",
    )


def render_step(step, data, errors=None):
    return render_template(
        "intake/form.html",
        step=step, steps=STEPS, data=data, errors=errors or {},
        age_groups=AGE_GROUPS, duration_choices=DURATION_CHOICES, yes_no=YES_NO,
        fields=FIELDS,
    ), (400 if errors else 200)


@intake.route("/intake", methods=["GET", "POST"])
def start():
    if request.method == "GET":
        return render_step(1, {name: "" for name in FIELDS})

    data = clean(request.form)
    try:
        step = int(request.form.get("step", "1"))
    except ValueError:
        step = 1
    step = max(1, min(step, LAST_STEP))

    action = request.form.get("action", "next")
    if action == "back":
        return render_step(max(1, step - 1), data)
    if action.startswith("edit-") and action[5:].isdigit():
        # "Edit" links on the review page jump back to one step, answers kept.
        return render_step(max(1, min(int(action[5:]), LAST_STEP - 1)), data)

    # Re-validate this step and every earlier one (catches skipped or edited steps).
    bad_step, errors = first_invalid_step(data, step)
    if bad_step:
        return render_step(bad_step, data, errors)

    # Branch once the screening questions (step 2) are answered.
    if step >= 2:
        reason = out_of_scope_reason(data)
        if reason:
            return redirect(url_for("intake.not_a_fit", reason=reason))

    if step < LAST_STEP:
        return render_step(step + 1, data)

    record = build_intake(data)
    db.session.add(record)
    db.session.commit()
    session["intake_submitted_id"] = record.intake_id
    return redirect(url_for("intake.submitted"))


@intake.route("/intake/not-a-fit")
def not_a_fit():
    from app.public import RESOURCES
    reason = request.args.get("reason")
    message = OUT_OF_SCOPE_REASONS.get(reason, OUT_OF_SCOPE_REASONS["age"])
    return render_template("intake/not_a_fit.html", message=message, resources=RESOURCES)


@intake.route("/intake/submitted")
def submitted():
    intake_id = session.get("intake_submitted_id")
    if intake_id is None:
        abort(404)
    return render_template("intake/submitted.html", intake_id=intake_id)