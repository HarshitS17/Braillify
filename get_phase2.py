import json

with open("/Users/saini/.gemini/antigravity/brain/bb75f285-e0d6-4fac-b7d5-0a2d352b2a29/.system_generated/logs/transcript_full.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        if data.get("type") == "USER_INPUT":
            content = data.get("content", "")
            if "PHASE 2" in content:
                # Find Phase 2 section
                lines = content.split('\n')
                in_phase_2 = False
                phase_2_text = []
                for l in lines:
                    if l.startswith("PHASE 2"):
                        in_phase_2 = True
                    elif l.startswith("PHASE 3") and in_phase_2:
                        break
                    
                    if in_phase_2:
                        phase_2_text.append(l)
                print("\n".join(phase_2_text))
                break
