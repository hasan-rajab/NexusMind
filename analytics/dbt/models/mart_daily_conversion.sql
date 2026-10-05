with daily as (
    select cohort_day, count(*) as sessions, sum(converted) as completed,
           sum(converted)::double/count(*) as completion_rate
    from {{ ref('fct_sessions') }} where matured=1 group by cohort_day
)
select *, 100*(completion_rate-lag(completion_rate) over(order by cohort_day))
       as change_vs_previous_observed_day_pp
from daily
