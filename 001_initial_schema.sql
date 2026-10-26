-- 001: initial schema (Users, Intakes, IntakeStatusHistory, ContactSubmissions)
CREATE TABLE IF NOT EXISTS "Users" (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    email          VARCHAR(120) NOT NULL UNIQUE,
    password_hash  VARCHAR(256) NOT NULL,
    full_name      VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS "Intakes" (
    intake_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name          VARCHAR(100) NOT NULL,
    client_email         VARCHAR(120) NOT NULL,
    client_phone         VARCHAR(20)  NOT NULL,
    age_category         VARCHAR(50)  NOT NULL,
    disability_details   TEXT NOT NULL,
    tried_accommodations BOOLEAN NOT NULL,
    case_summary         TEXT NOT NULL,
    status               VARCHAR(20) DEFAULT 'New',
    pdf_filename         VARCHAR(255),
    submitted_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "IntakeStatusHistory" (
    history_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id   INTEGER REFERENCES "Intakes" (intake_id),
    old_status  VARCHAR(20) NOT NULL,
    new_status  VARCHAR(20) NOT NULL,
    changed_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "ContactSubmissions" (
    contact_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_name   VARCHAR(100) NOT NULL,
    sender_email  VARCHAR(120) NOT NULL,
    message       TEXT NOT NULL,
    submitted_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
