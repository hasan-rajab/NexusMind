"""Opt-in local event capture. Never stores prompts, responses or raw identities."""
from __future__ import annotations

import csv
import hashlib
import hmac
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from analytics.pipeline import FIELDS, SQL, validate_event

LOG=logging.getLogger(__name__)


def capture(event_name, *, tenant_id, session_id, subject_id=None, role='assistant', latency_ms=None):
    database=os.environ.get('NEXUS_ANALYTICS_DB')
    secret=os.environ.get('NEXUS_ANALYTICS_KEY')
    if not database or not secret or not session_id:
        return False
    try:
        def pseudonym(kind, value):
            payload=f'{kind}\0{tenant_id}\0{value}'.encode()
            return hmac.new(secret.encode(),payload,hashlib.sha256).hexdigest()
        subject=pseudonym('subject',subject_id or session_id)
        session=pseudonym('session',session_id)
        timestamp=datetime.now(timezone.utc).isoformat()
        row={'event_id':uuid.uuid4().hex,'subject_id':subject,'session_id':session,
             'timestamp':timestamp,'event_name':event_name,'segment':str(role)[:128],
             'variant':'','latency_ms':latency_ms,'cost_usd':''}
        value=validate_event(row)
        path=Path(database);path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(path,timeout=.25) as db:
            db.executescript((SQL/'schema.sql').read_text())
            with db:
                existing=db.execute("SELECT subject_id FROM raw_events WHERE session_id=? AND event_name='session_started' LIMIT 1",(session,)).fetchone()
                if existing and existing[0]!=subject:
                    raise ValueError('Session subject changed')
                if not existing:
                    start=list(value);start[0]='start-'+session;start[4]='session_started';start[7]=None
                    db.execute('INSERT OR IGNORE INTO raw_events VALUES (?,?,?,?,?,?,?,?,?)',start)
                db.execute('INSERT INTO raw_events VALUES (?,?,?,?,?,?,?,?,?)',value)
        return True
    except (OSError,ValueError,sqlite3.Error):
        # Analytics must not break the product request. Log a generic error only.
        LOG.warning('Local analytics event was not recorded')
        return False


def export_events(database, destination):
    """Snapshot captured events into the same CSV contract as the offline pipeline."""
    path=Path(destination);path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(f'file:{Path(database).resolve()}?mode=ro',uri=True) as db, path.open('w',newline='') as handle:
        db.row_factory=sqlite3.Row
        writer=csv.DictWriter(handle,fieldnames=FIELDS,lineterminator='\n');writer.writeheader()
        for row in db.execute('SELECT * FROM raw_events ORDER BY event_ts,event_id'):
            value=dict(row);value['timestamp']=datetime.fromtimestamp(value.pop('event_ts'),timezone.utc).isoformat()
            writer.writerow(value)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();export_events(args.database,args.out)
