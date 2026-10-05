select event_id, subject_id, session_id,
       epoch(cast(timestamp as timestamptz))::bigint as event_ts,
       event_name, segment, nullif(variant, '') as variant, latency_ms, cost_usd
from {{ ref('demo_events') }}
