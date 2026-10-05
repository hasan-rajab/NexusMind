import csv
import sqlite3

import pytest

from analytics.demo import generate_events
from analytics.pipeline import export_report, load_events, make_report
from analytics.statistics import compare_conversion, srm_pvalue, wilson_interval
from analytics.telemetry import capture, export_events


def event(identifier, subject='a', session='s', timestamp='2026-09-01T00:00:00Z', name='session_started', variant='A'):
    return dict(event_id=identifier,subject_id=subject,session_id=session,timestamp=timestamp,
                event_name=name,segment='web',variant=variant,latency_ms='',cost_usd='')


def test_funnel_orders_events_keeps_nonconverters_and_excludes_immature_sessions(tmp_path):
    events=[event('1'), event('2',timestamp='2026-09-01T00:10:00Z',name='query_started'),
            event('3',timestamp='2026-09-01T00:05:00Z',name='query_completed'),
            event('4',subject='b',session='b'),
            event('5',subject='c',session='c',variant='B'),
            event('6',subject='c',session='c',variant='B',timestamp='2026-09-01T00:01:00Z',name='query_started'),
            event('7',subject='c',session='c',variant='B',timestamp='2026-09-01T00:02:00Z',name='query_completed'),
            event('8',subject='late',session='late',variant='B',timestamp='2026-09-01T23:40:00Z')]
    db=tmp_path/'a.sqlite';load_events(db,events,'2026-09-02T00:00:00Z')
    report=make_report(db,permutations=200)
    assert report['funnel']['eligible_sessions']==3
    assert report['funnel']['queried']==2 and report['funnel']['completed']==1
    assert report['funnel']['excluded_immature_sessions']==1
    assert report['experiment']['subjects_a']==2 and report['experiment']['subjects_b']==1


def test_returning_sessions_do_not_change_first_exposure_conversion_or_ab_sample(tmp_path):
    events=[event('1'),event('2',session='return',timestamp='2026-09-01T03:00:00Z'),
            event('3',session='return',timestamp='2026-09-01T03:01:00Z',name='query_started'),
            event('4',session='return',timestamp='2026-09-01T03:02:00Z',name='query_completed'),
            event('5',subject='b',session='b',variant='B')]
    path=tmp_path/'a.sqlite';load_events(path,events,'2026-09-02T00:00:00Z')
    report=make_report(path,permutations=200)
    assert report['funnel']['completed']==1
    assert report['experiment']['subjects_a']==1 and report['experiment']['completed_a']==0


@pytest.mark.parametrize('case',['conflicting_id','crossed_arm','crossed_session','orphan','future','naive','invalid_cost'])
def test_input_contracts_reject_corrupted_or_biased_input(tmp_path,case):
    events=[event('1')]
    if case=='conflicting_id': events.append(event('1',subject='b'))
    if case=='crossed_arm': events.append(event('2',session='new',variant='B'))
    if case=='crossed_session': events.append(event('2',subject='b'))
    if case=='orphan': events=[event('1',name='query_completed')]
    if case=='future': events=[event('1',timestamp='2027-01-01T00:00:00Z')]
    if case=='naive': events=[event('1',timestamp='2026-09-01T00:00:00')]
    if case=='invalid_cost': events[0]['cost_usd']='nan'
    with pytest.raises(ValueError): load_events(tmp_path/'a.sqlite',events,'2026-09-02T00:00:00Z')


def test_duplicate_events_and_reload_are_idempotent(tmp_path):
    path=tmp_path/'a.sqlite';events=[event('1'),event('1')]
    for _ in range(2):
        load_events(path,events,'2026-09-02T00:00:00Z')
        assert make_report(path,permutations=200)['unique_events']==1


def test_statistics_detect_srm_and_handle_zero_baseline_without_invented_relative_lift():
    assert srm_pvalue(50,50)==pytest.approx(1)
    assert srm_pvalue(99,1)<.01
    lo,hi=wilson_interval(0,10);assert lo==0 and 0<hi<1
    subjects=[dict(subject_id=f'a{i}',variant='A',converted=0) for i in range(10)]
    subjects += [dict(subject_id=f'b{i}',variant='B',converted=1) for i in range(10)]
    report=compare_conversion(subjects,permutations=200)
    assert report['relative_lift_pct'] is None and report['absolute_lift_pp']==100
    assert report['absolute_lift_ci95_pp'][0]>0
    assert report==compare_conversion(subjects,permutations=200)
    with pytest.raises(ValueError): compare_conversion(subjects+subjects[:1],permutations=200)


def test_demo_is_reproducible_and_report_exports_have_explicit_provenance(tmp_path):
    events=generate_events(100,42);assert events==generate_events(100,42)
    db=tmp_path/'demo.sqlite';load_events(db,events,'2026-10-02T00:00:00Z',provenance='SYNTHETIC DEMO')
    report=export_report(db,tmp_path,permutations=200)
    assert report['unique_subjects']==100 and report['provenance']=='SYNTHETIC DEMO'
    assert report['experiment']['subjects_a']+report['experiment']['subjects_b']==100
    assert 'SYNTHETIC DEMO' in (tmp_path/'dashboard.html').read_text()
    assert (tmp_path/'mart_segments.csv').exists()


def test_opt_in_telemetry_pseudonymizes_identity_and_exports_pipeline_contract(tmp_path,monkeypatch):
    path=tmp_path/'live.sqlite';monkeypatch.delenv('NEXUS_ANALYTICS_DB',raising=False)
    assert not capture('query_started',tenant_id='private-tenant',session_id='private-session')
    monkeypatch.setenv('NEXUS_ANALYTICS_DB',str(path));monkeypatch.setenv('NEXUS_ANALYTICS_KEY','private-key')
    assert capture('query_started',tenant_id='private-tenant',session_id='private-session',subject_id='private-user')
    assert capture('query_completed',tenant_id='private-tenant',session_id='private-session',subject_id='private-user',latency_ms=10)
    assert not capture('query_completed',tenant_id='private-tenant',session_id='private-session',subject_id='different-user')
    export_events(path,tmp_path/'live.csv')
    content=(tmp_path/'live.csv').read_text()
    assert all(secret not in content for secret in ['private-tenant','private-session','private-user','private-key'])
    with (tmp_path/'live.csv').open(newline='') as handle: events=list(csv.DictReader(handle))
    load_events(tmp_path/'snapshot.sqlite',events,'2099-01-01T00:00:00Z')
    assert make_report(tmp_path/'snapshot.sqlite',permutations=200)['funnel']['completed']==1
