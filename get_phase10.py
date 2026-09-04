import json

with open("/Users/saini/.gemini/antigravity/brain/bb75f285-e0d6-4fac-b7d5-0a2d352b2a29/.system_generated/logs/transcript_full.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        if data.get("type") == "USER_INPUT":
            content = data.get("content", "")
            if "PHASE 10" in content and "PHASE 11" in content:
                lines = content.split('\n')
                in_phase = False
                text = []
                for l in lines:
                    if l.startswith("PHASE 10"):
                        in_phase = True
                    elif l.startswith("PHASE 11") and in_phase:
                        break
                    if in_phase:
                        text.append(l)
                print("\n".join(text))
                break
