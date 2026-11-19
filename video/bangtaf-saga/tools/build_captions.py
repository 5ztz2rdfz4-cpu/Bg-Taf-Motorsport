"""Builds compositions/captions.html from the corrected transcript.
Source times are in the raw clip; SEGMENTS map them onto the edited timeline."""
import json, html
FPS = 30
def fr(t): return round(t * FPS) / FPS
# (src_start, src_end) of each kept piece, in edit order
SEGMENTS = [(1.88, 10.05), (10.62, 11.92), (14.18, 19.40), (20.00, 25.40), (25.80, 27.62), (32.68, 36.65)]
SEGMENTS = [(fr(a), fr(b)) for a, b in SEGMENTS]
# corrected words: (text, src_start, src_end, highlight)
W = [
 ("Gen",1.95,2.20,1),("Strawberry",2.20,2.55,1),("sekarang",2.55,2.98,0),("kalau",2.98,3.63,0),("nak",3.63,3.95,0),("keluar",3.95,4.51,0),
 ("mesti",4.51,5.39,0),("nak",5.39,5.57,0),("kena",5.57,5.83,0),("tanya",5.83,6.17,0),("mak",6.17,6.31,1),("ayah",6.31,6.51,1),("dulu",6.51,6.69,0),
 ("nak",6.69,7.11,0),("pinjam",7.11,7.39,1),("kereta",7.39,7.87,0),("mak,",7.87,8.17,1),("ayah,",8.31,8.93,1),("abang,",8.93,9.51,1),("akak.",9.55,9.97,1),
 ("Sampai",10.66,10.90,1),("bila",10.90,11.08,1),("korang",11.08,11.30,0),("nak",11.30,11.42,0),("macam",11.42,11.60,0),("ni?",11.60,11.88,0),
 ("So",14.25,14.45,0),("sekarang",14.45,14.90,0),("ni",14.90,15.22,0),("ada",15.22,15.78,0),("kereta",15.78,16.66,0),("yang",16.66,16.88,0),
 ("mampu",16.88,17.20,1),("milik",17.20,17.50,1),("iaitu",17.50,17.92,0),("Saga",17.92,18.34,1),("MC3",18.34,19.18,1),
 ("bulanan",20.06,21.00,0),("hanya",21.00,21.46,0),("serendah",21.46,22.24,0),("RM400",22.24,22.66,1),("lebih",22.66,23.02,1),("sahaja",23.02,23.50,0),
 ("korang",23.50,23.92,0),("dah",23.92,24.02,0),("boleh",24.02,24.22,0),("pakai",24.22,24.56,1),("dah",24.56,24.76,0),("kereta",24.76,25.10,0),("ni.",25.10,25.32,0),
 ("Low",25.85,26.02,1),("maintenance,",26.02,26.40,1),("jimat",26.66,26.92,1),("minyak",26.92,27.50,1),
 ("Kalau",32.72,32.91,0),("kata",32.91,33.21,0),("korang",33.21,33.47,0),("nak",33.47,33.57,0),("dapatkan",33.57,33.89,0),("kereta",33.89,34.21,0),("Saga",34.21,34.45,1),("ni,",34.45,34.71,0),
 ("boleh",34.71,35.19,0),("terus",35.19,35.45,0),("tekan",35.45,35.93,1),("beg",35.93,36.11,1),("biru.",36.11,36.55,1),
]
# group sizes in words, in order
GROUPS = [2,2,2,3,4,3,2,2, 3,3, 3,3,2,3, 2,3,1, 3,4, 2,2, 3,2,3, 3,2]
def to_out(t):
    off = 0.0
    for a, b in SEGMENTS:
        if a - 0.05 <= t <= b + 0.05:
            return off + min(max(t, a), b) - a
        off += b - a
    raise ValueError(t)
words = [dict(text=t, s=round(to_out(s), 3), e=round(to_out(e), 3), hl=h) for t, s, e, h in W]
assert sum(GROUPS) == len(words), (sum(GROUPS), len(words))
groups, i = [], 0
for n in GROUPS:
    groups.append(words[i:i+n]); i += n
total = sum(b - a for a, b in SEGMENTS)
cut_points, off = [], 0.0
for a, b in SEGMENTS:
    cut_points.append((round(off, 4), a, round(b - a, 4))); off += b - a
json.dump(dict(segments=cut_points, talk_end=round(total, 4), words=words), open("tools/edit_map.json", "w"), indent=1)
# ---- HTML
rows, js = [], []
for gi, g in enumerate(groups):
    start = max(0.12, g[0]["s"] - 0.06)
    nxt = groups[gi+1][0]["s"] - 0.06 if gi + 1 < len(groups) else total
    end = min(max(g[-1]["e"] + 0.25, start + 0.5), nxt, total)
    spans = " ".join(f'<span class="w{" hl" if w["hl"] else ""}" id="cw{gi}_{k}">{html.escape(w["text"])}</span>'
                    for k, w in enumerate(g))
    rows.append(f'    <div class="cg" id="cg{gi}">{spans}</div>')
    js.append(f'  show("#cg{gi}", {start:.3f}, {end:.3f}, [{",".join(f"{w["s"]:.3f}" for w in g)}]);')
out = open("compositions/captions.tpl.html").read()
out = out.replace("<!--GROUPS-->", "\n".join(rows)).replace("//CALLS", "\n".join(js))
open("compositions/captions.html", "w").write(out)
print("talk_end", round(total, 3))
for c in cut_points: print("seg out@%.3f src@%.3f dur %.3f" % c)
for w in words: print(f'{w["text"]}:{w["s"]:.2f}', end="  ")
print()
