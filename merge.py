#!/usr/bin/env python3
# =============================================================================
#  merge.py — Merge two news_dataset.csv files (yours + friend's)
#  Automatically removes duplicates using the content_hash column.
#
#  USAGE:
#    1. Put both CSV files in this folder
#    2. Change the file names below if needed
#    3. Run:  python merge.py
# =============================================================================

import csv

# ── Change these file names to match your actual files ───────────────────────
files = [
    "news_dataset.csv",         # your file
    "friends_data.csv",         # your friend's file (rename to match)
]

output = "merged_final.csv"     # the output merged file name
# ─────────────────────────────────────────────────────────────────────────────

fields = ["id", "title", "text", "source", "publish_date",
          "category", "label", "url", "content_hash"]

seen  = set()
rows  = []
skipped = 0

print(f"\nMerging {len(files)} files...")

for fname in files:
    count = 0
    try:
        with open(fname, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                h = row.get("content_hash", "").strip()
                if h and h not in seen:
                    seen.add(h)
                    rows.append(row)
                    count += 1
                else:
                    skipped += 1
        print(f"  ✅ {fname}: {count} rows added")
    except FileNotFoundError:
        print(f"  ❌ {fname}: FILE NOT FOUND — skipping")

# Re-number IDs from 1
for i, row in enumerate(rows, 1):
    row["id"] = i

# Save merged output
with open(output, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

# Summary
from collections import Counter
label_counts = Counter(row.get("label", "?") for row in rows)

print(f"\n{'='*50}")
print(f"  ✅  MERGE COMPLETE")
print(f"  Total unique rows : {len(rows)}")
print(f"  Duplicates removed: {skipped}")
print(f"  real  : {label_counts.get('real', 0)}")
print(f"  fake  : {label_counts.get('fake', 0)}")
print(f"  Saved to: {output}")
print(f"{'='*50}\n")
