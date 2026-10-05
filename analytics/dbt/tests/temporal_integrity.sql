select session_id from {{ ref('fct_sessions') }}
where first_query_at<cohort_ts
   or first_completion_at<first_query_at
   or first_completion_at>cohort_ts+{{ var('window_seconds') }}
   or (converted=1 and queried=0)
