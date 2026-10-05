"""Load pseudonymous event CSVs, execute SQL marts, export BI data and reports."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from analytics.statistics import compare_conversion

SQL = Path(__file__).parent/'sql'
EVENTS = {'session_started','query_started','query_completed','query_failed','feedback_submitted'}
FIELDS = ['event_id','subject_id','session_id','timestamp','event_name','segment','variant','latency_ms','cost_usd']


def epoch(value):
    timestamp=datetime.fromisoformat(value.replace('Z','+00:00'))
    if timestamp.tzinfo is None:
        raise ValueError('Timestamp requires an explicit timezone')
    return int(timestamp.timestamp())


def validate_event(row):
    identifiers=[]
    for name in ['event_id','subject_id','session_id','segment']:
        value=str(row.get(name,'')).strip()
        if not value or len(value)>128 or '\x00' in value:
            raise ValueError(f'Invalid {name}')
        identifiers.append(value)
    event=row.get('event_name'); variant=row.get('variant') or None
    if event not in EVENTS or variant not in (None,'A','B'):
        raise ValueError('Unknown event or variant')
    numbers=[]
    for name in ['latency_ms','cost_usd']:
        value=row.get(name)
        number=None if value in (None,'') else float(value)
        if number is not None and (number<0 or not math.isfinite(number)):
            raise ValueError(f'Invalid {name}')
        numbers.append(number)
    return (identifiers[0],identifiers[1],identifiers[2],epoch(row['timestamp']),event,
            identifiers[3],variant,*numbers)


def load_events(database, events, as_of, window_minutes=60, provenance='imported pseudonymous events'):
    if window_minutes<=0:
        raise ValueError('Positive funnel window required')
    values=[validate_event(row) for row in events]
    if not values:
        raise ValueError('No events to load')
    cutoff=epoch(as_of)
    if any(row[3]>cutoff for row in values):
        raise ValueError('Event timestamp is after the analysis cutoff')
    path=Path(database); path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as db:
        db.executescript((SQL/'schema.sql').read_text())
        with db:
            db.execute('DELETE FROM raw_events'); db.execute('DELETE FROM run_settings')
            for row in values:
                old=db.execute('SELECT * FROM raw_events WHERE event_id=?',(row[0],)).fetchone()
                if old and old!=row:
                    raise ValueError('Event ID reused with conflicting payload')
                db.execute('INSERT OR IGNORE INTO raw_events VALUES (?,?,?,?,?,?,?,?,?)',row)
            conflicts=db.execute('SELECT session_id FROM raw_events GROUP BY session_id '
                                 'HAVING COUNT(DISTINCT subject_id)>1 OR COUNT(DISTINCT variant)>1').fetchall()
            crossed=db.execute('SELECT subject_id FROM raw_events WHERE variant IS NOT NULL '
                               'GROUP BY subject_id HAVING COUNT(DISTINCT variant)>1').fetchall()
            orphans=db.execute("SELECT DISTINCT session_id FROM raw_events EXCEPT SELECT session_id FROM raw_events WHERE event_name='session_started'").fetchall()
            if conflicts or crossed or orphans:
                raise ValueError('Session identity/variant conflicts, crossed experiment arms, or missing session start')
            db.execute('INSERT INTO run_settings VALUES (1,?,?,?)',(cutoff,window_minutes*60,provenance))
        db.executescript((SQL/'models.sql').read_text())
    return len(values)


def rows(db, query, parameters=()):
    db.row_factory=sqlite3.Row
    return [dict(row) for row in db.execute(query,parameters)]


def percentile(values, fraction):
    if not values:
        return None
    ordered=sorted(values); position=(len(ordered)-1)*fraction
    lo=int(position); hi=min(lo+1,len(ordered)-1)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(position-lo)


def make_report(database, source_sha256=None, permutations=5000):
    with sqlite3.connect(database) as db:
        setting=rows(db,'SELECT * FROM run_settings')[0]
        funnel=rows(db,'SELECT COUNT(*) AS sessions,SUM(matured) AS eligible_sessions,'
                    'SUM(CASE WHEN matured=1 THEN queried ELSE 0 END) AS queried,'
                    'SUM(CASE WHEN matured=1 THEN converted ELSE 0 END) AS completed FROM fct_funnel')[0]
        funnel['excluded_immature_sessions']=funnel['sessions']-funnel['eligible_sessions']
        n=funnel['eligible_sessions']
        funnel['completion_rate']=funnel['completed']/n if n else None
        funnel['query_rate']=funnel['queried']/n if n else None
        subjects=rows(db,'SELECT * FROM mart_experiment_subjects ORDER BY subject_id')
        attempts=rows(db,"SELECT event_name,COUNT(*) AS n FROM raw_events WHERE event_name IN ('query_started','query_failed','query_completed') GROUP BY event_name")
        counts={row['event_name']:row['n'] for row in attempts}
        latencies=[row['latency_ms'] for row in rows(db,"SELECT latency_ms FROM raw_events WHERE event_name='query_completed' AND latency_ms IS NOT NULL")]
        retention=rows(db,"""WITH cohorts AS (
          SELECT subject_id,MIN(event_ts) AS first_ts FROM raw_events WHERE event_name='session_started' GROUP BY subject_id
        ), eligible AS (SELECT * FROM cohorts WHERE first_ts <= (SELECT as_of-8*86400 FROM run_settings)),
        activity AS (SELECT DISTINCT c.subject_id FROM eligible c JOIN raw_events e USING(subject_id)
          WHERE e.event_name='query_completed' AND e.event_ts >= c.first_ts+7*86400 AND e.event_ts < c.first_ts+8*86400)
        SELECT (SELECT COUNT(*) FROM eligible) AS eligible_subjects,COUNT(*) AS returned_subjects FROM activity""")[0]
        retention['retention_rate']=retention['returned_subjects']/retention['eligible_subjects'] if retention['eligible_subjects'] else None
        variant_guardrails=[]
        for arm in ['A','B']:
            observations=rows(db,"""SELECT e.* FROM raw_events e
              JOIN mart_experiment_subjects c USING(subject_id)
              CROSS JOIN run_settings r
              WHERE c.variant=? AND e.session_id=c.first_session_id
                AND e.event_ts BETWEEN c.first_exposure_ts AND c.first_exposure_ts+r.window_seconds
                AND e.event_name IN ('query_started','query_completed','query_failed')""",(arm,))
            attempts_n=sum(r['event_name']=='query_started' for r in observations)
            completed_n=sum(r['event_name']=='query_completed' for r in observations)
            failures_n=sum(r['event_name']=='query_failed' for r in observations)
            finished=[r for r in observations if r['event_name'] in ('query_completed','query_failed')]
            costs=[r['cost_usd'] for r in finished if r['cost_usd'] is not None]
            arm_latencies=[r['latency_ms'] for r in finished if r['event_name']=='query_completed' and r['latency_ms'] is not None]
            variant_guardrails.append({'variant':arm,'query_attempts':attempts_n,'completed':completed_n,
                'failures':failures_n,'failure_rate':failures_n/attempts_n if attempts_n else None,
                'completed_latency_p95_ms':percentile(arm_latencies,.95),
                'completed_latency_observations':len(arm_latencies),'completed_latency_missing':completed_n-len(arm_latencies),
                'attempts_with_cost':len(costs),'finished_attempts_missing_cost':len(finished)-len(costs),
                'cost_usd_per_completed_response':sum(costs)/completed_n if completed_n and len(costs)==len(finished) else None})
        return {'variant_guardrails':variant_guardrails,'provenance':setting['provenance'],'as_of':datetime.fromtimestamp(setting['as_of'],timezone.utc).isoformat(),
                'source_sha256':source_sha256,'window_minutes':setting['window_seconds']/60,
                'unique_events':db.execute('SELECT COUNT(*) FROM raw_events').fetchone()[0],
                'unique_subjects':db.execute('SELECT COUNT(DISTINCT subject_id) FROM raw_events').fetchone()[0],
                'funnel':funnel,'segments':rows(db,'SELECT * FROM mart_segments ORDER BY segment'),
                'daily':rows(db,'SELECT * FROM mart_daily_conversion ORDER BY cohort_day'),
                'day7_retention':retention,'experiment':compare_conversion(subjects,permutations=permutations),
                'guardrails':{'query_attempts':counts.get('query_started',0),'query_completions':counts.get('query_completed',0),'query_failures':counts.get('query_failed',0),
                             'failure_rate':counts.get('query_failed',0)/counts['query_started'] if counts.get('query_started') else None,
                             'completed_latency_observations':len(latencies),'completed_latency_missing':counts.get('query_completed',0)-len(latencies),'completed_latency_p95_ms':percentile(latencies,.95)},
                'notes':['Funnel steps are ordered and bounded by the configured window; immature sessions are excluded.',
                         'A/B inference counts independent subjects once, including subjects who never complete.',
                         'Synthetic demo lift is not a measured customer, revenue or deployment outcome.',
                         'Imported observational A/B labels do not establish randomization; verify allocation and exposure.',
                         'Latency covers completed queries; failures and missing latency are reported separately.']}


def export_report(database, outdir, source_sha256=None, permutations=5000):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    report=make_report(database,source_sha256,permutations)
    (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    with sqlite3.connect(database) as db:
        for view in ['mart_segments','mart_daily_conversion','mart_experiment_subjects']:
            data=rows(db,f'SELECT * FROM {view}')
            # The subject-level mart remains local for audit; do not publish identifiers.
            if view=='mart_experiment_subjects':
                continue
            with (out/f'{view}.csv').open('w',newline='') as handle:
                if data:
                    writer=csv.DictWriter(handle,fieldnames=list(data[0]),lineterminator='\n');writer.writeheader();writer.writerows(data)
    write_dashboard(report,out/'dashboard.html')
    return report


def write_dashboard(report, path):
    payload=json.dumps(report,allow_nan=False).replace('<','\\u003c')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEXUS Product Analytics</title><style>
body{font:16px system-ui;margin:auto;max-width:1080px;padding:32px;background:#f5f7fb;color:#17243b}h1{margin-bottom:8px}
.label{background:#e2ecff;padding:12px;border-radius:8px}.cards{display:flex;gap:14px;flex-wrap:wrap;margin:22px 0}
.card{padding:20px;background:white;border:1px solid #d8e0ee;border-radius:10px;min-width:175px}.value{font-size:28px;font-weight:650}
table{width:100%;border-collapse:collapse;background:white}td,th{text-align:left;padding:10px;border-bottom:1px solid #e1e7f0}
section{margin:26px 0}.bar{display:block;height:12px;background:#335dc8;border-radius:4px}small{color:#57677e}select{padding:8px}
</style><h1>NEXUS Product Analytics</h1><p id="provenance" class="label"></p><p id="scope"></p><div id="cards" class="cards"></div>
<section><h2>Ordered operational funnel</h2><div id="funnel"></div></section><section><h2>Segment diagnosis</h2>
<label>Segment <select id="segment"><option value="all">All segments</option></select></label><table><thead><tr><th>Segment</th><th>Eligible sessions</th><th>Completion</th><th>Rate</th></tr></thead><tbody id="segments"></tbody></table></section>
<section><h2>Experiment and guardrails</h2><p id="experiment"></p><p id="guardrails"></p><table><thead><tr><th>Variant</th><th>Attempts</th><th>Failure rate</th><th>p95 ms</th><th>Cost/completion USD</th></tr></thead><tbody id="arm-guardrails"></tbody></table></section>
<section><h2>Daily cohort trend</h2><table><thead><tr><th>UTC cohort day</th><th>Sessions</th><th>Completed</th><th>Rate</th></tr></thead><tbody id="daily"></tbody></table></section>
<section><h2>Interpretation</h2><ul id="notes"></ul></section><script type="application/json" id="data">PAYLOAD</script><script>
const d=JSON.parse(document.getElementById('data').textContent),f=d.funnel;
const pct=x=>x===null?'n/a':(100*x).toFixed(1)+'%',txt=(id,s)=>document.getElementById(id).textContent=s;
txt('provenance',d.provenance);txt('scope',d.unique_events+' events · '+d.unique_subjects+' subjects · '+d.window_minutes+' minute window · cutoff '+d.as_of);
for(const [name,value] of [['Eligible sessions',f.eligible_sessions],['Completion rate',pct(f.completion_rate)],['Immature excluded',f.excluded_immature_sessions],['Day 7 retention',pct(d.day7_retention.retention_rate)]]){
 const box=document.createElement('div');box.className='card';const title=document.createElement('div'),v=document.createElement('div');title.textContent=name;v.className='value';v.textContent=value;box.append(title,v);document.getElementById('cards').append(box);}
for(const [name,n] of [['Session started',f.eligible_sessions],['Query started',f.queried],['Query completed',f.completed]]){const p=document.createElement('p');p.textContent=name+' — '+n;const b=document.createElement('span');b.className='bar';b.style.width=(f.eligible_sessions?100*n/f.eligible_sessions:0)+'%';p.append(b);document.getElementById('funnel').append(p);}
function renderSegments(){const body=document.getElementById('segments');body.replaceChildren();for(const r of d.segments.filter(r=>document.getElementById('segment').value==='all'||r.segment===document.getElementById('segment').value)){const tr=document.createElement('tr');for(const v of [r.segment,r.sessions,r.completed,pct(r.completion_rate)]){const td=document.createElement('td');td.textContent=v;tr.append(td);}body.append(tr);}}
for(const r of d.segments){const option=document.createElement('option');option.value=r.segment;option.textContent=r.segment;document.getElementById('segment').append(option);}document.getElementById('segment').onchange=renderSegments;renderSegments();
const e=d.experiment;txt('experiment',e.status==='insufficient_arms'?'No complete A/B comparison.':e.subjects_a+' A / '+e.subjects_b+' B subjects; absolute lift '+e.absolute_lift_pp.toFixed(2)+' percentage points; 95% CI ['+e.absolute_lift_ci95_pp.map(x=>x.toFixed(2)).join(', ')+']; permutation p='+e.two_sided_permutation_pvalue.toFixed(4)+'; SRM p='+e.srm_pvalue.toFixed(4)+'. '+e.decision);
txt('guardrails','Query failures: '+d.guardrails.query_failures+'/'+d.guardrails.query_attempts+' ('+pct(d.guardrails.failure_rate)+'); completed-query p95 latency: '+d.guardrails.completed_latency_p95_ms+' ms.');
for(const r of d.variant_guardrails){const tr=document.createElement('tr');for(const v of [r.variant,r.query_attempts,pct(r.failure_rate),r.completed_latency_p95_ms===null?'n/a':r.completed_latency_p95_ms.toFixed(1),r.cost_usd_per_completed_response===null?'missing cost data':r.cost_usd_per_completed_response.toFixed(5)]){const td=document.createElement('td');td.textContent=v;tr.append(td);}document.getElementById('arm-guardrails').append(tr);}
for(const r of d.daily){const tr=document.createElement('tr');for(const v of [r.cohort_day,r.sessions,r.completed,pct(r.completion_rate)]){const td=document.createElement('td');td.textContent=v;tr.append(td);}document.getElementById('daily').append(tr);}
for(const n of d.notes){const li=document.createElement('li');li.textContent=n;document.getElementById('notes').append(li);}
</script></html>'''
    Path(path).write_text(page.replace('PAYLOAD',payload))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events',required=True);parser.add_argument('--as-of',required=True)
    parser.add_argument('--database',default='data/analytics.sqlite');parser.add_argument('--outdir',default='reports/analytics')
    parser.add_argument('--window-minutes',type=int,default=60);parser.add_argument('--provenance',default='imported pseudonymous events; randomization unverified')
    args=parser.parse_args();path=Path(args.events)
    with path.open(newline='') as handle: events=list(csv.DictReader(handle))
    load_events(args.database,events,args.as_of,args.window_minutes,args.provenance)
    report=export_report(args.database,args.outdir,hashlib.sha256(path.read_bytes()).hexdigest())
    print(json.dumps({k:report[k] for k in ['provenance','unique_events','unique_subjects','funnel','experiment']},indent=2))


if __name__=='__main__':
    main()
