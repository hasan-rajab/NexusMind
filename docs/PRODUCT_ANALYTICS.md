# Product analytics: question, metric, experiment and decision

## Question

Where does the NEXUS operational journey lose users, and would guided onboarding improve completed queries without increasing failure, latency or cost? This extension connects the RAG service to SQL/Python analytics. It provides an offline experiment harness and optional local service telemetry; it does not claim a deployed customer A/B experiment.

## Reproduce the synthetic case study

```bash
python -m analytics.demo
```

The standard-library pipeline generates 800 simulated subjects with seed 42, creates a SQLite warehouse and writes a report, dashboard and aggregate CSVs under `reports/analytics_demo/`. Open `dashboard.html` locally. The dashboard has segment filtering, ordered funnel counts, daily trends, cohort retention, experiment uncertainty and guardrails. Committed labelled outputs are under [`analytics/`](analytics/).

The simulator assigns A/B independently with 50:50 probability. Its parameters deliberately give B higher query initiation and lower failure, but higher latency and cost. Parameters are recorded in `report.json`; the observed demo lift demonstrates analysis, not a discovered customer improvement.

| Metric | Unit and denominator | Definition |
|---|---|---|
| Query initiation | Matured sessions | First query starts within 60 minutes of session start |
| Completion | Matured sessions | A completion follows initiation within the same 60-minute window |
| Primary experimental conversion | Subjects, once each | Completion in the subject's first exposed session |
| Day-7 retention | Subjects with 8 full days of follow-up | A completed query occurs 7–8 days after first session start |
| Failure | Started query attempts | `query_failed` events divided by `query_started` events |
| p95 latency | Completed queries with latency | Linear-interpolated 95th percentile of observed completion latency |
| Cost per completed response | First-exposure attempts/completions | Cost of completed and failed attempts divided by completions; omitted if any finished-attempt cost is missing |

Partial windows are excluded from funnel/experiment denominators and counted explicitly. Stage ordering prevents a completion before the first query from counting. Returning sessions cannot inflate the A/B sample or retroactively change first-session conversion.

## SQL and data contracts

`analytics/sql/schema.sql` defines the raw event layer and run settings. `models.sql` builds the ordered funnel fact and daily, segment and subject-level marts using CTEs, LEFT JOINs, GROUP BY, ROW_NUMBER and LAG. LEFT JOIN preserves users who never progress. An inner join here would bias conversion upward.

The ETL rejects conflicting duplicate IDs, crossed experiment arms, session/subject conflicts, missing session starts, naive timestamps, events after the analysis cutoff and invalid cost/latency. Identical repeated events deduplicate. Reloading the same source is idempotent, with the refresh inside one data transaction. UTC timestamps, the fixed cutoff, source SHA-256 and provenance appear in the report.

This is a lightweight SQLite warehouse with SQL models and tests. It demonstrates analytics engineering workflows without representing dbt, LookML, Airflow or GCP as implemented tools.

## Statistical design

The primary metric is pre-specified first-exposure completion. Use independent subjects as the experimental unit. Report an absolute percentage-point difference, a Newcombe 95% confidence interval, and a two-sided permutation test with 5,000 shuffles and a fixed seed. Relative lift is absent when the baseline rate is zero.

An exact binomial sample-ratio-mismatch check assumes independent Bernoulli 50:50 assignment; p < 0.01 flags allocation for investigation. It is not an SRM model for stratified/blocked assignment. Imported A/B labels are observational unless randomization/exposure are independently established. The confidence interval/permutation test do not prove causality from observational labels.

Guardrails are descriptive, separated by variant and bounded to first exposure. Multiple exploratory metrics do not become independent confirmatory hypothesis tests. Production use needs an experiment duration/sample-size plan, reliable exposure assignment, interference checks and a stopping policy.

## Observed demo interpretation

The deterministic sample contains **2,611 events**, **800 subjects**, **985 sessions**, and **984 mature sessions**. First-exposure assignment is **391 A / 409 B**. A completes **265/391** and B **335/409**; the demo difference is **14.13 percentage points**, with a 95% interval of **8.14–20.02 points**. The SRM p-value is about **0.548**.

Segment inspection shows lower initiation/completion on mobile. The simulator authors that difference; it is a diagnostic example, not evidence of a real mobile defect. B also has higher p95 completion latency (~3,694 ms vs ~3,074 ms) and cost per completed response (~$0.01229 vs ~$0.00645). A sensible decision is to investigate those tradeoffs before considering rollout. These figures are simulated, and no real revenue, savings or conversion improvement is claimed.

## Import real pseudonymous events

Required CSV columns: `event_id,subject_id,session_id,timestamp,event_name,segment,variant,latency_ms,cost_usd`. Optional numeric values/variant may be blank. IDs must already be pseudonymous; do not import names, emails, prompts or answers.

```bash
python -m analytics.pipeline --events private/events.csv \
  --as-of 2026-10-05T00:00:00Z --outdir reports/real_snapshot
```

Choose an explicit cutoff after the collection period. Do not reuse synthetic demo provenance for imported data. Aggregate exports/dashboard contain no subject identifiers; the subject-level audit mart remains local.

## Optional service telemetry

Set `NEXUS_ANALYTICS_DB` and a private random `NEXUS_ANALYTICS_KEY` to enable local capture. Both are blank by default. The `/chat` stream records start, completion or failure, and server-observed streaming latency. Nonempty completed streams count as completion; provider errors, empty responses and interrupted streams do not become successful completions. Telemetry errors do not break the user request.

Tenant/session/client subject tokens are HMAC-pseudonymized. No prompt, response or raw identity is recorded. Supply a stable pseudonymous `analytics_subject_id` in chat requests to connect sessions; otherwise the session is the fallback subject, and counts must not be described as distinct registered users. No production A/B assignment or treatment is added by telemetry.

```bash
python -m analytics.telemetry --database private/live.sqlite --out private/events.csv
python -m analytics.pipeline --events private/events.csv --as-of 2026-10-05T00:00:00Z
```

The existing interaction logger now defaults to the repository `data/logs` directory and still respects `NEXUSMIND_LOG_DIR`; importing the API no longer assumes a writable Kaggle filesystem. Interaction logs are separate from the content-free analytics store.

Use a different database for the offline snapshot so the ETL refresh does not overwrite ongoing capture. Keep operational telemetry out of Git; generated local reports/databases are ignored. Existing API access controls and retrieval-role checks remain tested.

Defensible CV wording: “Built a SQL/Python product-analytics warehouse with ordered funnels, cohort retention, segmentation and user-level A/B inference; validated on 2,611 labelled synthetic events from 800 simulated users and integrated optional pseudonymous service telemetry.” Do not describe the simulated lift as a customer/business outcome.
