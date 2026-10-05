{% docs __overview__ %}
# NEXUS product analytics

This public warehouse contains synthetic event data, never owner documents or visitor identifiers.
The fixture has 800 simulated subjects with independent Bernoulli assignment to A and B.
The primary metric is completion within 60 minutes of first exposure. Each subject is counted once;
fully unobserved windows are excluded. Session funnels are a separate diagnostic denominator.

Seed → typed staging → ordered session facts → subject, segment and daily marts.
Data tests check identifiers, categories, session identity, assignment and temporal order.
The export script verifies DuckDB results against the independently implemented SQLite pipeline.
Statistical methods include Wilson intervals, a Newcombe difference interval, exact SRM and a seeded
two-sided permutation test. Subgroups are exploratory. Lift in this simulation is not real business impact.
{% enddocs %}
