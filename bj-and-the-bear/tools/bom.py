#!/usr/bin/env python3
"""Bill of materials from an MPD: counts (part, colour), expanding submodels.

usage: bom.py MODEL.mpd OUT.csv [--root NAME]
Also writes a BrickLink wanted-list XML next to the CSV (same name, .xml).
LDraw ids are used as BrickLink ids; a few known differences are mapped.
"""
import argparse
import collections
import csv
import os

import ldr

COLOURS = {  # LDraw code: (name, BrickLink colour id)
    0: ("Black", 11), 4: ("Red", 5), 15: ("White", 1), 19: ("Tan", 2),
    71: ("Light Bluish Gray", 86), 72: ("Dark Bluish Gray", 85),
    297: ("Pearl Gold", 115), 179: ("Flat Silver", 95), 47: ("Trans-Clear", 12),
    40: ("Trans-Black", 13), 14: ("Yellow", 3),
}
BL_ID = {  # LDraw -> BrickLink where they differ
    "3680c01": "3680c02", "3403c01": "3403c01", "32123a": "4265c",
    "3709b": "3709b", "6538a": "6538c", "2695": "2695", "2696": "2696",
}


def load(path):
    files, cur = {}, None
    with open(path) as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[:2] == ["0", "FILE"]:
                cur = " ".join(t[2:]).lower()
                files[cur] = []
            elif t[0] == "1" and cur:
                files[cur].append((int(t[1]), " ".join(t[14:]).lower()))
    return files


def count(files, name, colour=16, mult=1, out=None):
    out = out if out is not None else collections.Counter()
    for c, part in files[name]:
        c = colour if c == 16 else c
        if part in files:
            count(files, part, c, mult, out)
        else:
            out[(part, c)] += mult
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("out")
    ap.add_argument("--root")
    a = ap.parse_args()
    files = load(a.model)
    root = (a.root or next(iter(files))).lower()
    c = count(files, root)
    rows = []
    for (part, col), n in sorted(c.items(), key=lambda kv: (ldr.title(kv[0][0]), kv[0][1])):
        pid = part[:-4] if part.endswith(".dat") else part
        cname, _ = COLOURS.get(col, (f"LDraw {col}", None))
        rows.append((pid, BL_ID.get(pid, pid), ldr.title(part), cname, n))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ldraw_id", "bricklink_id", "description", "colour", "qty"])
        w.writerows(rows)
    xml = ["<INVENTORY>"]
    for pid, bl, _, cname, n in rows:
        cid = next((v[1] for k, v in COLOURS.items() if v[0] == cname), None)
        xml.append(f"  <ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>{bl}</ITEMID>"
                   + (f"<COLOR>{cid}</COLOR>" if cid is not None else "")
                   + f"<MINQTY>{n}</MINQTY></ITEM>")
    xml.append("</INVENTORY>")
    with open(os.path.splitext(a.out)[0] + ".xml", "w") as f:
        f.write("\n".join(xml) + "\n")
    print(f"{sum(n for *_, n in rows)} parts, {len(rows)} lots -> {a.out}")
