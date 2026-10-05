select event_id from {{ ref('stg_events') }}
where event_ts>epoch(cast('{{ var("analysis_cutoff") }}' as timestamptz))
   or latency_ms<0 or cost_usd<0
