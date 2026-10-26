from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

STATUSES = ["New", "In Review", "Contacted", "Archived"]
AGE_CATEGORIES = ["50-59", "60+", "Child Disability"]


class User(UserMixin, db.Model):
    """Staff account (Flask-Login)."""
    __tablename__ = "Users"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Intake(db.Model):
    __tablename__ = "Intakes"
    intake_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    age_category = db.Column(db.String(50), nullable=False, index=True)  # "50-59", "60+", "Child Disability"
    disability_details = db.Column(db.Text, nullable=False)
    tried_accommodations = db.Column(db.Boolean, nullable=False)
    case_summary = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="New", index=True)  # New, In Review, Contacted, Archived
    pdf_filename = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    history = db.relationship(
        "IntakeStatusHistory", backref="intake", cascade="all, delete-orphan",
        order_by="IntakeStatusHistory.changed_at",
    )


class IntakeStatusHistory(db.Model):
    __tablename__ = "IntakeStatusHistory"
    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    intake_id = db.Column(db.Integer, db.ForeignKey("Intakes.intake_id"))
    old_status = db.Column(db.String(20), nullable=False)
    new_status = db.Column(db.String(20), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactSubmission(db.Model):
    __tablename__ = "ContactSubmissions"
    contact_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
