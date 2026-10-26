"""Public-facing pages: Home, About, Practice Areas, Resources, Contact, How SS Works."""
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash

public = Blueprint("public", __name__)

START_TIME = datetime.now()
REQUEST_COUNT = 0


@public.before_app_request
def count_request():
    global REQUEST_COUNT
    REQUEST_COUNT += 1


@public.route("/api/health")
def health():
    """Health check endpoint (Task 3 requirement)."""
    return {
        "status": "ok",
        "uptime_seconds": int((datetime.now() - START_TIME).total_seconds()),
        "requests_served": REQUEST_COUNT,
    }, 200


@public.app_context_processor
def inject_year():
    return {"now_year": datetime.utcnow().year}


STAGES = [
    ("Application", "You file with the Social Security Administration (SSA). Most first applications are denied, often on paperwork or missing medical evidence, so a complete file matters."),
    ("Reconsideration", "A different SSA reviewer looks at your claim again. You have 60 days from the date of the denial notice to ask for this review."),
    ("Hearing", "You appear before an Administrative Law Judge, usually by phone or video. This is where testimony and medical records carry the most weight."),
    ("Appeals Council", "If the judge denies your claim, you can ask the Appeals Council to review it for legal or procedural errors."),
    ("Federal court", "The last step is a civil lawsuit in U.S. District Court asking a judge to review the SSA's final decision."),
]

RESOURCES = {
    "Legal aid": [
        ("LawHelp.org", "https://www.lawhelp.org", "Find free civil legal help by state."),
        ("Idaho Legal Aid Services", "https://idaholegalaid.org", "Free legal help for eligible Idahoans."),
        ("Legal Services Corporation: Get Legal Help", "https://www.lsc.gov/about-lsc/what-legal-aid/get-legal-help", "Locate a legal aid office near you."),
    ],
    "Social Security Administration": [
        ("SSA Disability Benefits", "https://www.ssa.gov/benefits/disability/", "Official overview, application, and appeal information."),
        ("my Social Security account", "https://www.ssa.gov/myaccount/", "Check your work credits, benefit estimates, and claim status."),
        ("SSA phone line: 1-800-772-1213", "tel:18007721213", "Weekday service; TTY 1-800-325-0778."),
    ],
    "Idaho disability resources": [
        ("Disability Rights Idaho", "https://disabilityrightsidaho.org", "Protection and advocacy for people with disabilities."),
        ("Idaho Council on Developmental Disabilities", "https://icdd.idaho.gov", "Support and information for families."),
        ("Idaho Department of Health and Welfare", "https://healthandwelfare.idaho.gov", "State benefits, Medicaid, and assistance programs."),
    ],
}


@public.route("/")
def home():
    return render_template("public/home.html")


@public.route("/about")
def about():
    return render_template("public/about.html")


@public.route("/practice-areas")
def practice_areas():
    return render_template("public/practice_areas.html", stages=STAGES)


@public.route("/resources")
def resources():
    return render_template("public/resources.html", resources=RESOURCES)


@public.route("/how-social-security-works")
def how_social_security_works():
    return render_template("public/how_social_security_works.html")


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@public.route("/contact", methods=["GET", "POST"])
def contact():
    form = {"sender_name": "", "sender_email": "", "message": ""}
    errors = {}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in form}
        if not form["sender_name"]:
            errors["sender_name"] = "Enter your name."
        if not EMAIL_RE.match(form["sender_email"]):
            errors["sender_email"] = "Enter an email address like name@example.com."
        if not form["message"]:
            errors["message"] = "Tell us how we can help."
        if not errors:
            from app import db
            from app.models import ContactSubmission
            db.session.add(ContactSubmission(**form))
            db.session.commit()
            flash("Thank you. We received your message and will reply by email.", "success")
            return redirect(url_for("public.contact"))
    return render_template("public/contact.html", form=form, errors=errors)
