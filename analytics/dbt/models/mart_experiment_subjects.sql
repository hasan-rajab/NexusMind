-- One independent subject, one first exposure, one binary outcome.
with exposures as (
    select *, row_number() over(partition by subject_id order by cohort_ts,session_id) as rn
    from {{ ref('fct_sessions') }} where variant is not null
)
select subject_id, variant, converted, segment, session_id as first_session_id,
       cohort_ts as first_exposure_ts
from exposures where rn=1 and matured=1
