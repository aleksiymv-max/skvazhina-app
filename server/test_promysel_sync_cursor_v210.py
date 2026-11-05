#!/usr/bin/env python3
"""Safe, read-only regression checks for Supabase cursor pagination and offline restore."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
code=(root/'supabase/functions/promysel-compat/index.ts').read_text(encoding='utf8')
assert 'if((fullRestore||latestRelevantSeq>Number(cursor))&&(!moreMeasurements||fullRestore)){' in code
assert 'stateDeliveredSeq=moreMeasurements?0:recoveredSeq;' in code
assert 'const moreMeasurements=(data?.length??0)>=200;' in code
assert 'Math.max(Number(cursor),lastMeasurementSeq,stateDeliveredSeq)' in code

def restore(records, state_sequence):
    """Simulate the Edge API's cursor over a 200-item page, asserting no skipped records."""
    cursor=0
    delivered=[]
    received_state=False
    for _ in range(100):
        page=[n for n in records if n>cursor][:200]
        full_restore=cursor==0
        more=len(page)>=200
        relevant=state_sequence>cursor
        state_sent=(full_restore or relevant) and (not more or full_restore)
        if state_sent:
            received_state=True
        state_cursor=0 if more or not state_sent else state_sequence
        next_cursor=max(cursor,page[-1] if page else cursor,state_cursor)
        assert next_cursor>=cursor
        delivered+=page
        if not page and (not relevant or state_sent):
            break
        if next_cursor==cursor:
            assert state_sent
            break
        cursor=next_cursor
    assert received_state,'Full recovery must deliver snapshot even when records exceed a page'
    assert delivered==records, f'Cursor skipped {len(records)-len(delivered)} measurements'
    return cursor

for count in [0,1,199,200,201,399,400,401,605,1000]:
    records=list(range(1,count+1))
    for state in [1,max(1,count//2),count+1,count+1000]:
        restore(records,state)
print('PASS offline recovery: no missed measurement page, all snapshots delivered (40 cases)')
print('PASS source matches safe cursor arithmetic on full restore')
