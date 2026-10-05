"""Deterministic synthetic onboarding experiment, never real customer evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from analytics.pipeline import FIELDS, export_report, load_events

DEMO_CUTOFF='2026-10-02T00:00:00Z'


def generate_events(subjects=800, seed=42):
    if subjects < 2:
        raise ValueError('Need at least two subjects')
    rng=random.Random(seed);events=[]; counter=0
    base=datetime(2026,9,1,tzinfo=timezone.utc)
    def emit(subject, session, when, name, segment, variant, latency='', cost=''):
        nonlocal counter
        counter+=1
        events.append(dict(zip(FIELDS,[f'demo-event-{counter:05d}',subject,session,when.isoformat(),name,segment,variant,latency,cost])))
    for number in range(subjects):
        subject=f'demo-subject-{number:04d}';session=f'demo-session-{number:04d}'
        start=base+timedelta(minutes=rng.randrange(24*24*60))
        variant=rng.choice(['A','B'])  # independent 50:50 Bernoulli allocation
        segment=rng.choice(['web','mobile'])
        emit(subject,session,start,'session_started',segment,variant)
        query_chance=.78 if variant=='A' else .86
        if segment=='mobile': query_chance-=.08
        if rng.random()<query_chance:
            query_time=start+timedelta(minutes=rng.randrange(1,20))
            emit(subject,session,query_time,'query_started',segment,variant)
            failed=rng.random()<(.08 if variant=='A' else .04)
            latency=round(rng.uniform(600,3200)*(1.2 if variant=='B' else 1),1)
            emit(subject,session,query_time+timedelta(seconds=latency/1000),
                 'query_failed' if failed else 'query_completed',segment,variant,latency,
                 .006 if variant=='A' else .012)
        # Repeat use exercises subject-level denominator and mature day-7 cohorts.
        if rng.random()<.24:
            later=start+timedelta(days=7,minutes=10); repeat=session+'-return'
            emit(subject,repeat,later,'session_started',segment,variant)
            emit(subject,repeat,later+timedelta(minutes=1),'query_started',segment,variant)
            emit(subject,repeat,later+timedelta(minutes=1,seconds=1),'query_completed',segment,variant,1000,.006)
    return events


def run_demo(outdir='reports/analytics_demo',subjects=800,seed=42):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    events=generate_events(subjects,seed)
    path=out/'events.csv'
    with path.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS,lineterminator='\n');writer.writeheader();writer.writerows(events)
    provenance=f'SYNTHETIC DEMO: {subjects} simulated subjects; seed {seed}; no customer/business outcome'
    load_events(out/'warehouse.sqlite',events,DEMO_CUTOFF,provenance=provenance)
    report=export_report(out/'warehouse.sqlite',out,hashlib.sha256(path.read_bytes()).hexdigest())
    report['generator']={'seed':seed,'subjects':subjects,'assignment':'50:50 independent Bernoulli',
                         'query_probability_a':.78,'query_probability_b':.86,'mobile_probability_adjustment':-.08,
                         'query_failure_probability_a':.08,'query_failure_probability_b':.04,
                         'cost_usd_per_attempt_a':.006,'cost_usd_per_attempt_b':.012,
                         'b_latency_multiplier':1.2,'return_probability':.24}
    (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ['provenance','unique_events','unique_subjects','funnel','experiment','guardrails']},indent=2))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir',default='reports/analytics_demo');parser.add_argument('--subjects',type=int,default=800)
    parser.add_argument('--seed',type=int,default=42);args=parser.parse_args()
    run_demo(args.outdir,args.subjects,args.seed)


if __name__=='__main__':
    main()
