select subject_id from {{ ref('stg_events') }}
where variant is not null group by subject_id having count(distinct variant)>1
