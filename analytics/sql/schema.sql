PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS raw_events (
    event_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    event_ts INTEGER NOT NULL,
    event_name TEXT NOT NULL CHECK(event_name IN ('session_started','query_started','query_completed','query_failed','feedback_submitted')),
    segment TEXT NOT NULL,
    variant TEXT CHECK(variant IN ('A','B') OR variant IS NULL),
    latency_ms REAL CHECK(latency_ms >= 0),
    cost_usd REAL CHECK(cost_usd >= 0)
);
CREATE INDEX IF NOT EXISTS events_session_time ON raw_events(session_id, event_ts);
CREATE INDEX IF NOT EXISTS events_subject_time ON raw_events(subject_id, event_ts);
CREATE TABLE IF NOT EXISTS run_settings (
    id INTEGER PRIMARY KEY CHECK(id=1), as_of INTEGER NOT NULL,
    window_seconds INTEGER NOT NULL CHECK(window_seconds > 0),
    provenance TEXT NOT NULL
);
