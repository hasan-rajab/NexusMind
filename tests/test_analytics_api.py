"""Real FastAPI streaming routes with provider adapters stubbed; no external LLM."""
import importlib.util
import sqlite3
import sys
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path,monkeypatch):
    orchestrator=ModuleType('orchestrator');orchestrator.stream=None
    rag=ModuleType('tools.rag');rag.get_stats=lambda:{};rag.ingest=lambda *_:'test-doc'
    monkeypatch.setitem(sys.modules,'orchestrator',orchestrator)
    monkeypatch.setitem(sys.modules,'tools.rag',rag)
    monkeypatch.setenv('NEXUS_ANALYTICS_DB',str(tmp_path/'api.sqlite'))
    monkeypatch.setenv('NEXUS_ANALYTICS_KEY','test-private-key')
    spec=importlib.util.spec_from_file_location('nexus_analytics_api_test',Path(__file__).resolve().parents[1]/'backend'/'app.py')
    api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    monkeypatch.setattr(api,'REQUIRE_API_KEY',False)
    monkeypatch.setattr(api,'audit_event',lambda *_:None)
    monkeypatch.setattr(api,'log_interaction',lambda **_:None)
    return TestClient(api.app),orchestrator,tmp_path/'api.sqlite'


def test_completed_stream_records_started_and_completed_without_content(client):
    http,provider,database=client
    async def stream(*args,**kwargs):
        yield {'turn_id':'test-turn'}
        yield {'chunk':'PRIVATE RESPONSE'}
    provider.stream=stream
    response=http.post('/chat',json={'query':'PRIVATE PROMPT','session_id':'private-session'})
    assert response.status_code==200 and '[DONE]' in response.text
    with sqlite3.connect(database) as db:
        assert sorted(row[0] for row in db.execute('SELECT event_name FROM raw_events'))==['query_completed','query_started','session_started']
    assert b'PRIVATE PROMPT' not in database.read_bytes() and b'PRIVATE RESPONSE' not in database.read_bytes()


def test_failed_stream_does_not_inflate_completion_rate(client):
    http,provider,database=client
    async def stream(*args,**kwargs):
        yield {'turn_id':'test-turn'}
        raise RuntimeError('provider failure')
    provider.stream=stream
    response=http.post('/chat',json={'query':'policy question','session_id':'session'})
    assert 'agent request failed' in response.text
    with sqlite3.connect(database) as db:
        assert [row[0] for row in db.execute("SELECT event_name FROM raw_events WHERE event_name IN ('query_completed','query_failed')")]==['query_failed']


@pytest.mark.parametrize('chunk',['','   '])
def test_empty_stream_is_not_a_completed_query(client,chunk):
    http,provider,database=client
    async def stream(*args,**kwargs):
        yield {'turn_id':'test-turn'}
        yield {'chunk':chunk}
    provider.stream=stream
    response=http.post('/chat',json={'query':'policy question','session_id':'session'})
    assert response.status_code==200
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM raw_events WHERE event_name='query_completed'").fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM raw_events WHERE event_name='query_failed'").fetchone()[0]==1
