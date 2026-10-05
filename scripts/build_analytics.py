"""Rebuild a public, synthetic dbt/DuckDB serving bundle; no credentials needed."""
from __future__ import annotations
import csv
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analytics.demo import generate_events, DEMO_CUTOFF
from analytics.pipeline import FIELDS, load_events, make_report
from analytics.statistics import compare_conversion, wilson_interval


def fetch(db, query, params=()):
    cursor=db.execute(query,params)
    names=[c[0] for c in cursor.description]
    return [dict(zip(names,r)) for r in cursor.fetchall()]


def main():
    import duckdb
    project=ROOT/'analytics/dbt'; out=ROOT/'docs/analytics/dbt'
    project.joinpath('seeds').mkdir(parents=True,exist_ok=True)
    out.mkdir(parents=True,exist_ok=True)
    events=generate_events(subjects=800,seed=42)
    seed=project/'seeds/demo_events.csv'
    with seed.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n'); writer.writeheader(); writer.writerows(events)
    for command in [('build',),('docs','generate')]:
        subprocess.run(['dbt',*command,'--profiles-dir',str(project),'--project-dir',str(project)],cwd=project,check=True)
    db=duckdb.connect(str(project/'warehouse.duckdb'),read_only=True)
    for segment in ['all','web','mobile']:
        selected=events if segment=='all' else [e for e in events if e['segment']==segment]
        reference=ROOT/'reports'/f'dbt_check_{segment}.sqlite'
        load_events(reference,selected,DEMO_CUTOFF,provenance='SYNTHETIC DEMO: 800 simulated subjects; seed 42; no customer/business outcome')
        report=make_report(reference,hashlib.sha256(seed.read_bytes()).hexdigest())
        clause='' if segment=='all' else ' AND segment=?'; params=() if segment=='all' else (segment,)
        subjects=fetch(db,'SELECT subject_id,variant,converted FROM mart_experiment_subjects WHERE 1=1'+clause+' ORDER BY subject_id',params)
        comparison=compare_conversion(subjects)
        assert comparison==report['experiment'], 'DuckDB/SQLite first-exposure outcome mismatch'
        funnel=fetch(db,'SELECT COUNT(*) AS sessions,SUM(matured) AS eligible_sessions,'
                     'SUM(CASE WHEN matured=1 THEN queried ELSE 0 END) AS queried,'
                     'SUM(CASE WHEN matured=1 THEN converted ELSE 0 END) AS completed FROM fct_sessions WHERE 1=1'+clause,params)[0]
        for key,value in funnel.items():
            assert value==report['funnel'][key], f'DuckDB/SQLite funnel mismatch: {key}'
        segments=fetch(db,'SELECT * FROM mart_segments WHERE 1=1'+clause+' ORDER BY segment',params)
        assert segments==report['segments'], 'DuckDB/SQLite segment mismatch'
        daily=fetch(db,"""WITH d AS (SELECT cohort_day,COUNT(*) AS sessions,SUM(converted) AS completed,
          SUM(converted)::DOUBLE/COUNT(*) AS completion_rate FROM fct_sessions WHERE matured=1"""+clause+""" GROUP BY cohort_day)
          SELECT *,100*(completion_rate-LAG(completion_rate) OVER(ORDER BY cohort_day)) AS change_vs_previous_observed_day_pp FROM d ORDER BY cohort_day""",params)
        for row in daily: row['cohort_day']=str(row['cohort_day'])
        assert daily==report['daily'], 'DuckDB/SQLite daily mismatch'
        report.update(segment=segment,experiment=comparison,segments=segments,daily=daily,
                      arm_ci95={'a':wilson_interval(comparison['completed_a'],comparison['subjects_a']),
                                'b':wilson_interval(comparison['completed_b'],comparison['subjects_b'])},
                      funnel_sql=(project/'models/fct_sessions.sql').read_text(),
                      warehouse='DuckDB 1.4.1; dbt-duckdb 1.10.0',
                      validation='dbt build data tests passed; funnel/subject/segment/daily equivalence with independent SQLite pipeline passed')
        (out/f'report_{segment}.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    db.close()
    for asset in ['catalog.json','run_results.json']:
        shutil.copyfile(project/'target'/asset,out/asset)
    manifest=json.loads((project/'target/manifest.json').read_text())
    # Public compact catalogue: model SQL and tested lineage, without the large
    # dbt macro library. Full original docs are retained in the CI artifact.
    keep=['unique_id','name','resource_type','description','columns','raw_code','compiled_code','depends_on','config']
    compact={key:manifest[key] for key in ['metadata','parent_map','child_map']}
    compact['nodes']={uid:{k:node[k] for k in keep if k in node} for uid,node in manifest['nodes'].items()}
    (out/'manifest.json').write_text(json.dumps(compact,indent=2)+'\n')
    shutil.copyfile(ROOT/'frontend/lineage.html',out/'index.html')
    print('Public synthetic dbt bundle built and independently verified for all/web/mobile.')


if __name__=='__main__': main()
