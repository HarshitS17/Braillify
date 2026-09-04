"""End-to-end API test of the DEPLOYED Braillify app (https://braillify.vercel.app).
Mirrors the exact call sequence the React UI makes:
create project -> upload real textbook page -> preprocess -> detect -> accept
-> workflow (extract..place) -> labels -> edit label (server re-translates
braille) -> validate -> export SVG -> export PDF.
"""
import json
import sys
import urllib.request
import uuid

BASE = "https://braillify.vercel.app"
FIXTURE = "/Users/saini/Downloads/TextileEd/backend/qa_fixtures/02_complex_biology.png"

results = []


def step(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}: {name} {detail}")


def req(path, method="GET", data=None, headers=None, raw=False):
    r = urllib.request.Request(BASE + path, method=method, data=data,
                               headers=headers or {})
    with urllib.request.urlopen(r, timeout=120) as resp:
        body = resp.read()
        return resp.status, (body if raw else json.loads(body))


# 1. create project
name = f"deployed-e2e-{uuid.uuid4().hex[:8]}"
st, proj = req("/api/projects", "POST", json.dumps({"name": name}).encode(),
               {"Content-Type": "application/json"})
pid = proj["id"]
step("create project", st in (200, 201) and pid, f"project={pid} status={st}")

# 2. upload real textbook page (multipart)
boundary = uuid.uuid4().hex
with open(FIXTURE, "rb") as f:
    img = f.read()
mp = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
      f"filename=\"02_complex_biology.png\"\r\nContent-Type: image/png\r\n\r\n").encode() + img + f"\r\n--{boundary}--\r\n".encode()
st, page = req(f"/api/projects/{pid}/pages", "POST", mp,
               {"Content-Type": f"multipart/form-data; boundary={boundary}"})
pgid = page["page_id"]
step("upload real textbook page", st == 200 and pgid,
     f"page={pgid} {page['width']}x{page['height']}")

# 3. preprocess
st, pre = req(f"/api/projects/{pid}/pages/{pgid}/preprocess", "POST", b"{}",
              {"Content-Type": "application/json"})
step("preprocess", st == 200, json.dumps(pre)[:80])

# 4. detect
st, cands = req(f"/api/projects/{pid}/pages/{pgid}/detect", "POST", b"{}",
                {"Content-Type": "application/json"})
step("diagram detection", st == 200 and len(cands) > 0,
     f"{len(cands)} candidate(s), top confidence={cands[0].get('confidence') if cands else 'n/a'}")

# 5. accept candidate (same as RegionEditor accept button)
st, saved = req(f"/api/projects/{pid}/pages/{pgid}/diagrams", "POST",
                json.dumps(cands).encode(), {"Content-Type": "application/json"})
did = saved[0]["id"] if isinstance(saved, list) and saved else None
step("accept candidate -> diagram saved", did is not None, f"diagram={did}")

# 6. run full pipeline workflow extract->place
st, wf = req(f"/api/projects/{pid}/pages/{pgid}/diagrams/{did}/workflow", "POST",
             json.dumps({"start_stage": "extract", "end_stage": "place", "debug": False}).encode(),
             {"Content-Type": "application/json"})
n_elem = len(wf.get("elements", []))
n_lab = len(wf.get("labels", []))
step("workflow extract->place (vectorize+simplify+analyze+braille+place)",
     st == 200 and n_elem > 0 and n_lab > 0, f"{n_elem} elements, {n_lab} labels")

# 7. labels persisted & readable
st, labels = req(f"/api/projects/{pid}/pages/{pgid}/diagrams/{did}/labels")
orig_text = labels[0]["text"] if labels else None
orig_braille = labels[0].get("braille") if labels else None
step("labels retrievable", st == 200 and len(labels) > 0,
     f"label[0]: text={orig_text!r} braille={orig_braille!r}")

# 8. human-in-the-loop edit: change text, server re-translates braille
lid = labels[0]["id"]
st, upd = req(f"/api/projects/{pid}/pages/{pgid}/diagrams/{did}/labels/{lid}", "PUT",
              json.dumps({"text": "Deployed E2E"}).encode(),
              {"Content-Type": "application/json"})
step("label edit persisted + server-side braille re-translation",
     st == 200 and upd["text"] == "Deployed E2E" and upd["braille"] != orig_braille,
     f"braille {orig_braille!r} -> {upd['braille']!r}")

# 9. validation
st, val = req(f"/api/projects/{pid}/pages/{pgid}/diagrams/{did}/validate")
step("validation engine", st == 200, f"{len(val.get('issues', []))} issue(s)")

# 10. export SVG and confirm the EDIT is in it
st, svg = req(f"/api/projects/{pid}/pages/{pgid}/diagrams/{did}/export/svg", "POST",
              json.dumps({"config": {}}).encode(),
              {"Content-Type": "application/json"}, raw=True)
braille_str = upd["braille"]["braille_unicode"] if isinstance(upd["braille"], dict) else upd["braille"]
has_edit = "Deployed E2E".encode() in svg or braille_str.encode() in svg
step("SVG export contains edited label + braille", st == 200 and has_edit,
     f"{len(svg)} bytes, edit present={has_edit}")
open("/tmp/deployed_export.svg", "wb").write(svg)

# 11. export PDF
st, pdf = req(f"/api/projects/{pid}/pages/{pgid}/diagrams/{did}/export/pdf", "POST",
              json.dumps({"config": {}}).encode(),
              {"Content-Type": "application/json"}, raw=True)
step("PDF export", st == 200 and pdf[:5] == b"%PDF-",
     f"{len(pdf)} bytes, header={pdf[:5]!r}")
open("/tmp/deployed_export.pdf", "wb").write(pdf)

# cleanup
try:
    req(f"/api/projects/{pid}", "DELETE")
except Exception:
    pass

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n===== DEPLOYED E2E: {passed}/{len(results)} steps passed =====")
sys.exit(0 if passed == len(results) else 1)
