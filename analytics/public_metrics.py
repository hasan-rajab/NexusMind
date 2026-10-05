"""Public aggregates: labelled synthetic reports and separate opt-in usage."""
import json
import time
from pathlib import Path

from analytics.pipeline import percentile

ROOT = Path(__file__).resolve().parents[1]


def synthetic_report(segment="all"):
    return json.loads((ROOT / "docs/analytics/dbt" / f"report_{segment}.json").read_text())


def live_summary(database):
    with database() as db:
        # Only fully observed one-hour windows. QA sessions are excluded by a
        # server-authenticated marker, never by a browser-supplied event field.
        rows = db.execute("""WITH starts AS (
          SELECT session_token, MIN(event_ts) AS start_ts FROM demo_events
          WHERE is_test=0 AND event_name='session_started' GROUP BY session_token
        ), queries AS (
          SELECT s.*, MIN(e.event_ts) AS query_ts FROM starts s LEFT JOIN demo_events e
          ON e.session_token=s.session_token AND e.is_test=0 AND e.event_name='query_started'
            AND e.event_ts BETWEEN s.start_ts AND s.start_ts+3600 GROUP BY s.session_token
        ) SELECT q.session_token, q.start_ts, q.query_ts, MIN(e.event_ts) AS complete_ts
          FROM queries q LEFT JOIN demo_events e ON e.session_token=q.session_token
            AND e.is_test=0 AND e.event_name='query_completed'
            AND e.event_ts BETWEEN q.query_ts AND q.start_ts+3600 GROUP BY q.session_token""").fetchall()
        mature = [r for r in rows if r["start_ts"] <= time.time()-3600]
        latencies = [r[0] for r in db.execute("SELECT latency_ms FROM demo_events WHERE is_test=0 AND event_name='query_completed' AND latency_ms IS NOT NULL")]
        counts = dict(db.execute("SELECT event_name,COUNT(*) FROM demo_events WHERE is_test=0 GROUP BY event_name"))
    n = len(mature)
    complete = sum(r["complete_ts"] is not None for r in mature)
    attempts = counts.get("query_started", 0)
    return {"provenance": "LIVE opt-in public-demo visits; internal QA excluded; observational, not an A/B experiment",
            "window_minutes": 60, "consented_visits": len(rows), "eligible_visits": n,
            "immature_visits": len(rows)-n, "queried": sum(r["query_ts"] is not None for r in mature),
            "completed": complete, "completion_rate": complete/n if n else None,
            "query_attempts": attempts, "failures": counts.get("query_failed",0),
            "completed_latency_p95_ms": percentile(latencies,.95),
            "status": "collecting" if not n else "observational_sample",
            "notes": "Visits are browser sessions, not unique people. Consent introduces selection bias. No prompts or responses are retained by this analytics store. Operational quota metadata is separate; 31-day retention."}
