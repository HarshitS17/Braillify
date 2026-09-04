"""Focused API smoke test for the editor persistence endpoints (QA regression)."""
import json, glob, os, urllib.request

diag_files = sorted(glob.glob('workspace/projects/*/diagrams/*/diagram.json'),
                    key=lambda p: os.path.getmtime(p), reverse=True)
for df in diag_files:
    d = json.load(open(df))
    if d.get('labels'):
        pid, did, page_id = d['project_id'], d['id'], d['page_id']
        break
else:
    raise SystemExit('NO_LABELED_DIAGRAM')
print('Using project', pid, 'page', page_id, 'diagram', did)

def req(method, path, body=None):
    r = urllib.request.Request(
        f'http://localhost:8000{path}', method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())

labels = req('GET', f'/api/projects/{pid}/pages/{page_id}/diagrams/{did}/labels')
lbl = labels[0]
print('BEFORE: text=%r source=%r' % (lbl['text'], lbl['source']))

# 1. Single-label text correction -> server must re-translate braille
upd = req('PUT', f'/api/projects/{pid}/pages/{page_id}/diagrams/{did}/labels/{lbl["id"]}',
          {'text': 'Heart Corrected'})
print('AFTER PUT: text=%r braille=%r dots=%r source=%r'
      % (upd['text'], upd['braille']['braille_unicode'], upd['braille']['braille_dots'], upd['source']))
assert upd['text'] == 'Heart Corrected', 'text not applied'
assert upd['source'] == 'manual', 'source not marked manual'
assert upd['braille']['braille_unicode'], 'braille not re-translated'

# 2. Verify persisted
lbl2 = req('GET', f'/api/projects/{pid}/pages/{page_id}/diagrams/{did}/labels')
assert any(l['text'] == 'Heart Corrected' for l in lbl2), 'text not persisted'
print('PERSISTED OK: %d labels' % len(lbl2))

# 3. Bulk replace: drop the last label (simulates delete sync)
shrunk = lbl2[:-1]
req('PUT', f'/api/projects/{pid}/pages/{page_id}/diagrams/{did}/labels', {'labels': shrunk})
after = req('GET', f'/api/projects/{pid}/pages/{page_id}/diagrams/{did}/labels')
d = req('GET', f'/api/projects/{pid}/pages/{page_id}/diagrams/{did}')
assert len(after) == len(lbl2) - 1, 'bulk replace count mismatch'
assert len(d['labels']) == len(shrunk), 'diagram.labels not updated'
assert not os.path.exists(f'workspace/projects/{pid}/labels/{lbl2[-1]["id"]}.json'), 'deleted label file still exists'
print('BULK DELETE OK: %d labels remain, file removed' % len(after))

# 4. Element-level update: remove one element
nelem = len(d['elements'])
req('PUT', f'/api/projects/{pid}/pages/{page_id}/diagrams/{did}', {'elements': d['elements'][:-1]})
d2 = req('GET', f'/api/projects/{pid}/pages/{page_id}/diagrams/{did}')
assert len(d2['elements']) == nelem - 1, 'element delete failed'
print('ELEMENT DELETE OK: %d -> %d elements' % (nelem, len(d2['elements'])))
print('ALL SMOKE TESTS PASSED')
