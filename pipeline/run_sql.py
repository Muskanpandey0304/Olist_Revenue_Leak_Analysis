"""Run every statement in a .sql file against data/olist.db and print results."""
import sqlite3, re, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
con = sqlite3.connect(root / "data" / "olist.db")
for q in open(sys.argv[1], encoding="utf-8").read().split(";"):
    q = re.sub(r"--[^\n]*", "", q).strip()
    if not q:
        continue
    cur = con.execute(q)
    print([d[0] for d in cur.description])
    for r in cur.fetchall():
        print(r)
    print()
