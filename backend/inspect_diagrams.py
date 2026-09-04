import json, glob

def diagram_for_project(pid):
    for d in glob.glob(f'workspace/projects/{pid}/diagrams/*/diagram.json'):
        with open(d) as f:
            return json.load(f)
    return None

for pid in ['426bd6a8-81a4-4164-9b9d-c757f6544022', 'db0a7713-24ea-4f5e-ac84-e05926e29b7f']:
    d = diagram_for_project(pid)
    if not d:
        print(pid, 'NO DIAGRAM')
        continue
    print('===', pid, 'status', d['status'], 'offset', d['page_offset_x'], d['page_offset_y'], 'bbox', d.get('source_bbox'))
    for el in d['elements']:
        g = el['geometry']
        brief = json.dumps(g)[:110]
        print(f"  {el['type']:14s} role={el['semantic_role']:10s} conf={el['confidence']:.2f} {brief}")
    print('  labels:', d['labels'])
    print('  log:', d['processing_log'])