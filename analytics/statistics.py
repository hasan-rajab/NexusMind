"""User-level proportion inference for two pre-specified experimental arms.

Permutation inference assumes random assignment and independent subjects.
A small p-value on the synthetic demo is not customer or revenue evidence.
"""
from __future__ import annotations

import math
import random
from statistics import NormalDist


def wilson_interval(successes, total, confidence=.95):
    if total <= 0 or not 0 <= successes <= total or not 0 < confidence < 1:
        raise ValueError('Invalid binomial counts or confidence')
    z = NormalDist().inv_cdf((1+confidence)/2); p = successes/total
    den = 1+z*z/total
    center = (p+z*z/(2*total))/den
    half = z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return (0. if successes == 0 else max(0.,center-half)), (1. if successes == total else min(1.,center+half))


def srm_pvalue(n_a, n_b):
    """Two-sided exact binomial SRM test for expected Bernoulli 50:50 allocation."""
    if n_a < 0 or n_b < 0 or n_a+n_b == 0:
        raise ValueError('Invalid allocation counts')
    n = n_a+n_b; tail = min(n_a,n_b)
    log_terms = [math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*math.log(2)
                 for k in range(tail+1)]
    largest = max(log_terms)
    return min(1., 2*math.exp(largest)*sum(math.exp(v-largest) for v in log_terms))


def compare_conversion(subjects, seed=42, permutations=5000):
    if permutations < 100:
        raise ValueError('Use at least 100 permutations')
    seen = set(); a=[]; b=[]
    for row in subjects:
        if row['subject_id'] in seen:
            raise ValueError('Duplicate experimental subject')
        seen.add(row['subject_id'])
        if row['variant'] not in ('A','B') or row['converted'] not in (0,1):
            raise ValueError('Invalid variant or binary conversion')
        (a if row['variant']=='A' else b).append(row['converted'])
    if not a or not b:
        return {'status':'insufficient_arms', 'subjects_a':len(a),'subjects_b':len(b)}
    n_a,n_b = len(a),len(b); success_a,success_b = sum(a),sum(b)
    rate_a,rate_b = success_a/n_a,success_b/n_b
    a_lo,a_hi = wilson_interval(success_a,n_a); b_lo,b_hi = wilson_interval(success_b,n_b)
    # Newcombe hybrid-score interval for the difference of independent proportions.
    diff = rate_b-rate_a
    lower = diff-math.sqrt((rate_b-b_lo)**2+(a_hi-rate_a)**2)
    upper = diff+math.sqrt((b_hi-rate_b)**2+(rate_a-a_lo)**2)
    rng = random.Random(seed); pooled=a+b; extreme=0
    for _ in range(permutations):
        rng.shuffle(pooled)
        shuffled_a=sum(pooled[:n_a]); shuffled_b=success_a+success_b-shuffled_a
        if abs(shuffled_b/n_b-shuffled_a/n_a) >= abs(diff)-1e-12:
            extreme+=1
    srm=srm_pvalue(n_a,n_b)
    return {'status':'allocation_warning' if srm<.01 else 'ok', 'experimental_unit':'subject',
            'subjects_a':n_a,'subjects_b':n_b,'completed_a':success_a,'completed_b':success_b,
            'rate_a':rate_a,'rate_b':rate_b,'absolute_lift_pp':100*diff,
            'relative_lift_pct':100*diff/rate_a if rate_a else None,
            'absolute_lift_ci95_pp':[100*lower,100*upper],
            'two_sided_permutation_pvalue':(extreme+1)/(permutations+1),
            'srm_pvalue':srm,'srm_expected_allocation':'50:50 Bernoulli',
            'seed':seed,'permutations':permutations,'primary_metric':'completion within the fixed session window',
            'decision':'investigate assignment before interpreting lift' if srm<.01 else
                       'demo/analysis result only; deployment needs real randomized exposure and guardrails'}
