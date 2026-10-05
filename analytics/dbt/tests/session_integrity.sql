select session_id from {{ ref('stg_events') }} group by session_id
having count(distinct subject_id)>1 or count(distinct segment)>1
    or count(distinct variant)>1
    or sum(case when event_name='session_started' then 1 else 0 end)=0
