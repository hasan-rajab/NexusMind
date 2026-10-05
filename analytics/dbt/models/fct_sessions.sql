-- Non-converters must stay in the denominator: LEFT JOIN, not INNER JOIN.
with ranked_starts as (
    select *, row_number() over(partition by session_id order by event_ts, event_id) as rn
    from {{ ref('stg_events') }} where event_name='session_started'
), starts as (
    select event_id, subject_id, session_id, event_ts, segment, variant,
           epoch(cast('{{ var("analysis_cutoff") }}' as timestamptz))::bigint as as_of,
           {{ var('window_seconds') }} as window_seconds
    from ranked_starts where rn=1
), queries as (
    select s.*, min(q.event_ts) as first_query_at
    from starts s left join {{ ref('stg_events') }} q
      on q.session_id=s.session_id and q.event_name='query_started'
      and q.event_ts between s.event_ts and least(s.event_ts+s.window_seconds,s.as_of)
    group by all
), completions as (
    select q.*, min(c.event_ts) as first_completion_at
    from queries q left join {{ ref('stg_events') }} c
      on c.session_id=q.session_id and c.event_name='query_completed'
      and c.event_ts between q.first_query_at and least(q.event_ts+q.window_seconds,q.as_of)
    group by all
)
select session_id, subject_id, event_ts as cohort_ts,
       cast(to_timestamp(event_ts) at time zone 'UTC' as date) as cohort_day,
       segment, variant, (event_ts <= as_of-window_seconds)::integer as matured,
       first_query_at, first_completion_at,
       (first_query_at is not null)::integer as queried,
       (first_completion_at is not null)::integer as converted
from completions
