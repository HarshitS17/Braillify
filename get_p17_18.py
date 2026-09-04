import json, re

with open("/Users/saini/.gemini/antigravity/brain/bb75f285-e0d6-4fac-b7d5-0a2d352b2a29/.system_generated/logs/transcript_full.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        if data.get("type") == "USER_INPUT":
            content = data.get("content", "")
            if "PHASE 17" in content and "PHASE 18" in content:
                lines = content.split('\n')
                in_17 = False; in_18 = False
                p17 = []; p18 = []
                for l in lines:
                    if l.startswith("PHASE 17"):
                        in_17 = True; in_18 = False
                    elif l.startswith("PHASE 18"):
                        in_18 = True; in_17 = False
                    elif re.match(r'^PHASE \d+', l):
                        in_17 = False; in_18 = False
                    elif "============" in l and not in_17 and not in_18:
                        continue
                    if in_17: p17.append(l)
                    if in_18: p18.append(l)
                print("=== PHASE 17 ===")
                print("\n".join(p17[:30]))
                print("\n=== PHASE 18 ===")
                print("\n".join(p18[:30]))
                break
