DROP VIEW IF EXISTS mart_daily_conversion;
DROP VIEW IF EXISTS mart_segments;
DROP VIEW IF EXISTS mart_experiment_subjects;
DROP VIEW IF EXISTS fct_funnel;
CREATE VIEW fct_funnel AS
WITH ranked_starts AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY event_ts,event_id) AS rn
    FROM raw_events WHERE event_name='session_started'
), starts AS (
    SELECT e.*, r.as_of, r.window_seconds,
           e.event_ts <= r.as_of-r.window_seconds AS matured
    FROM ranked_starts e CROSS JOIN run_settings r WHERE e.rn=1
), queries AS (
    SELECT s.*, MIN(q.event_ts) AS first_query_at
    FROM starts s LEFT JOIN raw_events q
      ON q.session_id=s.session_id AND q.event_name='query_started'
     AND q.event_ts BETWEEN s.event_ts AND MIN(s.event_ts+s.window_seconds,s.as_of)
    GROUP BY s.session_id
), completions AS (
    SELECT q.*, MIN(c.event_ts) AS first_completion_at
    FROM queries q LEFT JOIN raw_events c
      ON c.session_id=q.session_id AND c.event_name='query_completed'
     AND c.event_ts BETWEEN q.first_query_at AND MIN(q.event_ts+q.window_seconds,q.as_of)
    GROUP BY q.session_id
)
SELECT session_id,subject_id,event_ts AS cohort_ts,date(event_ts,'unixepoch') AS cohort_day,
       segment,variant,matured,first_query_at,first_completion_at,
       first_query_at IS NOT NULL AS queried, first_completion_at IS NOT NULL AS converted
FROM completions;

CREATE VIEW mart_segments AS
SELECT segment,COUNT(*) AS sessions,SUM(queried) AS queried,SUM(converted) AS completed,
       1.0*SUM(queried)/COUNT(*) AS query_rate,
       1.0*SUM(converted)/COUNT(*) AS completion_rate,
       1.0*SUM(converted)/NULLIF(SUM(queried),0) AS query_to_completion_rate
FROM fct_funnel WHERE matured=1 GROUP BY segment;

CREATE VIEW mart_daily_conversion AS
WITH daily AS (
    SELECT cohort_day,COUNT(*) AS sessions,SUM(converted) AS completed,
           1.0*SUM(converted)/COUNT(*) AS completion_rate
    FROM fct_funnel WHERE matured=1 GROUP BY cohort_day
)
SELECT *,100*(completion_rate-LAG(completion_rate) OVER(ORDER BY cohort_day))
       AS change_vs_previous_observed_day_pp
FROM daily;

-- Experimental unit is a SUBJECT, not a query or a session. Repeated sessions
-- never increase the A/B sample size. Matured sessions only; fixed window.
CREATE VIEW mart_experiment_subjects AS
WITH exposures AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY subject_id ORDER BY cohort_ts,session_id) AS rn
    FROM fct_funnel WHERE variant IS NOT NULL
)
SELECT subject_id,variant,converted,session_id AS first_session_id,cohort_ts AS first_exposure_ts
FROM exposures WHERE rn=1 AND matured=1;
