select segment, count(*) as sessions, sum(queried) as queried, sum(converted) as completed,
       sum(queried)::double/count(*) as query_rate,
       sum(converted)::double/count(*) as completion_rate,
       sum(converted)::double/nullif(sum(queried),0) as query_to_completion_rate
from {{ ref('fct_sessions') }} where matured=1 group by segment
