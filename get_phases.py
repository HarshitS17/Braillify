import json

with open("/Users/saini/.gemini/antigravity/brain/bb75f285-e0d6-4fac-b7d5-0a2d352b2a29/.system_generated/logs/transcript_full.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        if data.get("type") == "USER_INPUT":
            content = data.get("content", "")
            if "PHASE 1" in content and "PHASE 18" in content:
                print("Found total phases up to 18 (or more).")
                # let's extract all phase headers
                import re
                phases = re.findall(r'^PHASE \d+ — .*$', content, re.MULTILINE)
                for p in phases:
                    print(p)
                break
