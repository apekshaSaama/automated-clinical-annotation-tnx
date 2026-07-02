import json
import os

SOURCE_FILE = os.path.join(os.path.dirname(__file__), "smoking_notes.json")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "smoking")

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

for record in records:
    idx = record["idx"]
    note = record["note"]
    output_path = os.path.join(OUTPUT_DIR, f"{idx}.txt")
    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write(note)

print(f"Wrote {len(records)} note files to {OUTPUT_DIR}")
