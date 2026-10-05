# Public portfolio and analytics evidence

Entry point: https://nexusmind-production-3da9.up.railway.app/portfolio

## Visitor journeys

- `/demo`: read-only public case-study RAG; no API key or owner access is needed.
- `/demo/analytics`: interactive synthetic funnel, segment and A/B analysis; aggregate JSON download.
- `/demo/lineage/`: model SQL and dependency explorer using dbt-generated catalogue/manifest.
- `/demo/usage`: aggregate opt-in visitor events, separate from synthetic experiment results.

Owner endpoints keep their existing application-key requirement. A guest cookie is never an owner credential.
The public route fixes the Chroma tenant to `public-portfolio-sample` and role to `public_demo`, bypasses
the private orchestrator/tool execution, and makes one bounded provider call. The sample docs are public
and idempotently upserted at startup. Prompts and responses are not recorded in public analytics.

`PUBLIC_DEMO_ENABLED=true` enables the sandbox. Default quotas: five questions per 24-hour visit,
200 questions per UTC day across all visitors, three-second request spacing and 20 visit creations
per best-effort IP token per day. Limits are atomic in persistent SQLite. Cross-origin browser mutations
are refused. The cookie is Secure/HttpOnly/SameSite=Lax in production. QA visits marked with an owner-
authenticated test header never contribute to visitor aggregates. Analytics requires optional consent.
No experiment assignment takes place on the live site. Visits are not unique people, consent selection
bias exists, and immature one-hour windows are excluded. Metadata expires after 31 days at startup.

## Reproduce the warehouse

```bash
pip install -r requirements-analytics.txt
python scripts/build_analytics.py
```

This generates the 800-subject seed (seed 42), persists five SQL models in DuckDB, executes 19 dbt
data tests and exports three aggregate reports. Cutoff: 2026-10-02 UTC; funnel window: 60 minutes.
First-exposure outcome, funnel, segment and daily counts are compared against the independent SQLite
pipeline. Public output contains model SQL, test results and aggregate data. No visitor identifiers or
owner documents are exported. The full original dbt documentation is retained as a CI artifact; the
serving site uses a compact viewer over dbt metadata.

The generator deliberately makes B more likely to complete and also slower/more expensive. Its
significant simulated lift is not a measured business result. Subgroups are exploratory with no
multiplicity correction. A real rollout needs genuine randomized exposure, sample-size planning,
a stopping rule and latency/failure/cost guardrails agreed before observation.

## CV evidence and remaining factual limits

| Review gap | Implemented evidence | CV treatment |
|---|---|---|
| SQL not demonstrated | Ordered funnels with CTEs, LEFT JOIN, ROW_NUMBER and LAG; Telecom SQL load and prior-only trend marts | Name actual SQL transformations |
| Experimentation absent | Subject-level A/B simulation, Wilson/Newcombe intervals, permutation test, SRM and guardrails | Explicitly say 800 simulated subjects; no customer uplift |
| Weak +24h gain | Paired block-bootstrap interval includes zero | Lead with +1h; explain horizon limits in project |
| Anomaly denominator missing | 24 injected Telecom events; TP20 FP16 FN4 | Say injected events and count |
| Raw/model scope conflated | 200,908,858 raw scans; 30 cells, 38 days, 27,360 hourly rows | State both denominators |
| Projects off-target | NEXUS analytics first; Sentinel has temporal synthetic benchmark and error slices | Lead with analysis; compress AI engineering |
| Experience unquantified | Existing genuine workshop/stakeholder work | No invented attendance, revenue or time savings |
| Research off-target | Controlled experiments, statistical evaluation, resource efficiency | One transferable research line |
| BI/warehouse evidence absent | DuckDB/dbt pipeline, generated lineage, interactive aggregate dashboard and downloads | List tools only after actual build/test |

Undergraduate GPA is unconfirmed and is omitted. The MSc GPA 3.95/4.00 and expected January 2027
completion come from the current CV. February 2027 availability is the supplied application target.
Public demos establish usable software and analytical methods; they do not establish real adoption,
banking product outcomes or business impact before those outcomes are actually observed.
