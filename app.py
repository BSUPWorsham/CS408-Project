import os
import re
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
# Flash messages need a secret key. In production it comes from the
# environment (/etc/aplin-law.env); the fallback is for local development only.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

START_TIME = datetime.now()
REQUEST_COUNT = 0

FIRM = {
    "name": "Aplin Law",
    "tagline": "Social Security disability help for working people and their families",
    "city": "Boise, Idaho",
    # Placeholder contact details until the firm supplies real ones.
    "phone": "(208) 555-0142",
    "phone_href": "+12085550142",
    "email": "intake@aplinlaw.example",
    "hours": "Monday to Friday, 8:30 a.m. to 5:00 p.m. Mountain Time",
}

NAV = [
    ("index", "Home"),
    ("about", "About Us"),
    ("practice_areas", "Practice Areas"),
    ("social_security", "How Social Security Works"),
    ("resources", "Resource Center"),
    ("contact", "Contact"),
]

CLAIM_STAGES = [
    {
        "name": "Initial application",
        "icon": "bi-file-earmark-text",
        "summary": "You apply online, by phone, or at a local Social Security office. "
                   "A state agency (Disability Determination Services) gathers your "
                   "medical records and decides whether you meet the rules.",
        "tip": "List every doctor, clinic, and hospital you have seen, with dates. "
               "Missing records are one of the most common reasons claims are denied.",
    },
    {
        "name": "Reconsideration",
        "icon": "bi-arrow-repeat",
        "summary": "If you are denied, you can ask for a fresh review by a different "
                   "examiner at the same agency. New medical evidence can be added.",
        "tip": "You generally have 60 days from the date you receive a denial to appeal. "
               "Do not start over with a new application; appeal instead.",
    },
    {
        "name": "Hearing before a judge",
        "icon": "bi-person-video3",
        "summary": "An Administrative Law Judge hears your case, usually by video or phone. "
                   "You can testify about how your condition limits your daily life and work.",
        "tip": "This is the stage where many claims are won. A vocational expert often "
               "testifies about what work, if any, you could still do.",
    },
    {
        "name": "Appeals Council",
        "icon": "bi-bank",
        "summary": "If the judge denies your claim, the Appeals Council can review the "
                   "decision for legal or factual errors and may send it back for a new hearing.",
        "tip": "The Council looks for mistakes in the judge's decision, so the written "
               "argument matters more than new testimony.",
    },
    {
        "name": "Federal court",
        "icon": "bi-building-columns",
        "summary": "The last step is filing a civil case in U.S. District Court, "
                   "which reviews whether Social Security applied the law correctly.",
        "tip": "Federal court has its own filing rules and deadlines. Talk with an "
               "attorney before this step.",
    },
]

RESOURCES = [
    {
        "group": "Social Security Administration",
        "icon": "bi-shield-check",
        "links": [
            ("Apply for disability benefits", "https://www.ssa.gov/disability",
             "Start an SSDI or SSI application and check eligibility."),
            ("my Social Security account", "https://www.ssa.gov/myaccount/",
             "See your earnings record, work credits, and claim status."),
            ("Find your local office", "https://secure.ssa.gov/ICON/main.jsp",
             "Look up the Social Security office that serves your ZIP code."),
            ("Appeal a decision", "https://www.ssa.gov/disability/appeal",
             "Request reconsideration or a hearing after a denial."),
            ("Ticket to Work", "https://choosework.ssa.gov/",
             "Free employment support for people receiving disability benefits."),
        ],
    },
    {
        "group": "Legal aid and advocacy",
        "icon": "bi-people",
        "links": [
            ("Idaho Legal Aid Services", "https://www.idaholegalaid.org/",
             "Free civil legal help for low-income Idahoans."),
            ("DisAbility Rights Idaho", "https://disabilityrightsidaho.org/",
             "Idaho's protection and advocacy agency for people with disabilities."),
            ("National Disability Rights Network", "https://www.ndrn.org/",
             "Find the protection and advocacy agency in any state."),
            ("LawHelp.org", "https://www.lawhelp.org/",
             "Directory of free legal aid programs by state."),
        ],
    },
    {
        "group": "Work, health, and family support",
        "icon": "bi-heart-pulse",
        "links": [
            ("Idaho Division of Vocational Rehabilitation", "https://vr.idaho.gov/",
             "Job training and placement for people with disabilities."),
            ("Job Accommodation Network", "https://askjan.org/",
             "Free guidance on workplace accommodations for employees and employers."),
            ("Idaho Parents Unlimited", "https://ipulidaho.org/",
             "Support and training for families of children with disabilities."),
            ("USAGov Benefit Finder", "https://www.usa.gov/benefit-finder",
             "Find federal benefits you may qualify for."),
        ],
    },
]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.context_processor
def inject_globals():
    return {"firm": FIRM, "nav": NAV, "current_year": datetime.now().year}


@app.before_request
def count_request():
    global REQUEST_COUNT
    REQUEST_COUNT += 1


@app.route("/")
def index():
    return render_template("index.html", stages=CLAIM_STAGES)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/practice-areas")
def practice_areas():
    return render_template("practice_areas.html", stages=CLAIM_STAGES)


@app.route("/how-social-security-works")
def social_security():
    return render_template("social_security.html")


@app.route("/resources")
def resources():
    return render_template("resources.html", resources=RESOURCES)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = {"name": "", "email": "", "message": ""}
    errors = {}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in form}
        if not form["name"]:
            errors["name"] = "Please enter your name."
        elif len(form["name"]) > 100:
            errors["name"] = "Please keep your name under 100 characters."
        if not EMAIL_RE.match(form["email"]) or len(form["email"]) > 120:
            errors["email"] = "Please enter a valid email address."
        if len(form["message"]) < 10:
            errors["message"] = "Please tell us a little more (at least 10 characters)."
        if not errors:
            # Checkpoint 3: save to the ContactSubmissions table here.
            flash("Thank you. Your message was received and someone will reply "
                  "within one business day.", "success")
            return redirect(url_for("contact"))
    status = 400 if errors else 200
    return render_template("contact.html", form=form, errors=errors), status


@app.route("/intake")
def intake():
    # Checkpoint 4 replaces this with the multi-step intake form.
    return render_template("coming_soon.html", title="Free Case Review",
                           message="Our online case review form is being finished. "
                                   "In the meantime, call us or send a message and we "
                                   "will walk you through it.")


@app.route("/login")
def login():
    # Checkpoint 3 replaces this with Flask-Login authentication.
    return render_template("coming_soon.html", title="Staff Sign In",
                           message="Staff sign-in will be available soon.")


@app.route("/api/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": int((datetime.now() - START_TIME).total_seconds()),
        "requests_served": REQUEST_COUNT,
    }, 200


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=port,
            debug=os.environ.get("FLASK_DEBUG") == "1")
