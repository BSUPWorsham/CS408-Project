-- 002: indexes for the dashboard filters (status, age category, date range)
CREATE INDEX IF NOT EXISTS "ix_Intakes_status"       ON "Intakes" (status);
CREATE INDEX IF NOT EXISTS "ix_Intakes_age_category" ON "Intakes" (age_category);
CREATE INDEX IF NOT EXISTS "ix_Intakes_submitted_at" ON "Intakes" (submitted_at);
