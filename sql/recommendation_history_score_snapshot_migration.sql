-- Adds server-side score snapshots used by preference learning.
-- Run once on existing Supabase/PostgreSQL databases created before this change.

ALTER TABLE recommendation_history
    ADD COLUMN IF NOT EXISTS price_score NUMERIC(5, 2);

ALTER TABLE recommendation_history
    ADD COLUMN IF NOT EXISTS waiting_time_score NUMERIC(5, 2);

ALTER TABLE recommendation_history
    ADD COLUMN IF NOT EXISTS distance_score NUMERIC(5, 2);

ALTER TABLE recommendation_history
    ADD COLUMN IF NOT EXISTS facilities_score NUMERIC(5, 2);
