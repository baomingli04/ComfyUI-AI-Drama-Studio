# -*- coding: utf-8 -*-
import json
import sqlite3

conn = sqlite3.connect(r"D:\SC\web4\django\db.sqlite3")
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT skill_id, name, category, description, source, created_at FROM api_skill ORDER BY id"
).fetchall()
conn.close()
out = []
for r in rows:
    out.append({k: r[k] for k in r.keys()})
print(json.dumps(out, ensure_ascii=False, indent=2))
