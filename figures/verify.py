from __future__ import annotations

import json
import math
import re
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SCALE = 3
MARGIN = 30
MIN_GAP = 16
SEG_FAIL = 4.0
SEG_WARN = 7.0
PAD_WARN = 4.0

MEASURE_JS = """
const svg = document.querySelector('svg');
const sr = svg.getBoundingClientRect();
const vb = svg.viewBox.baseVal;
const sx = vb.width / sr.width, sy = vb.height / sr.height;
const out = [];
svg.querySelectorAll('text').forEach(el => {
  const r = el.getBoundingClientRect();
  out.push({txt: el.textContent,
            x: (r.left - sr.left) * sx, y: (r.top - sr.top) * sy,
            w: r.width * sx, h: r.height * sy,
            size: parseFloat(getComputedStyle(el).fontSize),
            weight: getComputedStyle(el).fontWeight,
            family: getComputedStyle(el).fontFamily});
});
const pre = document.createElement('pre');
pre.id = 'report';
pre.textContent = '<<<JSON' + JSON.stringify(out) + 'JSON>>>';
document.body.appendChild(pre);
"""


def _html(svg_text: str, script: str = "") -> str:
    tail = f"<script>{script}</script>" if script else ""
    return (
        "<html><head><meta charset='utf-8'><style>html,body{margin:0;padding:0;"
        "background:#fff}svg{display:block}</style></head><body>"
        f"{svg_text}{tail}</body></html>"
    )


PROFILE = tempfile.mkdtemp(prefix="chrome-fig-")
BASE_FLAGS = ["--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
              "--no-default-browser-check", "--disable-background-networking",
              "--disable-sync", f"--user-data-dir={PROFILE}", "--hide-scrollbars"]


def _chrome(args: list[str], expect_file: Path | None = None,
            marker: str | None = None, deadline: float = 60.0) -> str:
    """Chrome headless does the work then declines to exit; poll, then kill it."""
    proc = subprocess.Popen([CHROME] + BASE_FLAGS + args,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    chunks: list[str] = []
    if marker:
        reader = threading.Thread(target=lambda: chunks.append(proc.stdout.read()), daemon=True)
        reader.start()
    start = time.time()
    try:
        while time.time() - start < deadline:
            if expect_file and expect_file.exists():
                size = expect_file.stat().st_size
                time.sleep(0.4)
                if size and expect_file.stat().st_size == size:
                    return ""
            if marker and any(marker in c for c in chunks):
                break
            if proc.poll() is not None:
                break
            time.sleep(0.25)
    finally:
        proc.kill()
        proc.wait()
    return "".join(chunks)


def render_png(svg_path: Path, png_path: Path, w: int, h: int) -> None:
    if png_path.exists():
        png_path.unlink()
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
        fh.write(_html(svg_path.read_text()))
        page = fh.name
    _chrome([f"--screenshot={png_path}", f"--window-size={w},{h}",
             f"--force-device-scale-factor={SCALE}", f"file://{page}"], expect_file=png_path)
    if not png_path.exists():
        raise SystemExit(f"render failed: {png_path}")


def measure_text(svg_path: Path) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
        fh.write(_html(svg_path.read_text(), MEASURE_JS))
        page = fh.name
    dom = _chrome(["--virtual-time-budget=3000", "--dump-dom", f"file://{page}"],
                  marker="JSON&gt;&gt;&gt;")
    m = re.search(r"&lt;&lt;&lt;JSON(.*?)JSON&gt;&gt;&gt;", dom, re.S) or \
        re.search(r"<<<JSON(.*?)JSON>>>", dom, re.S)
    if not m:
        raise SystemExit("measurement failed: no report in DOM")
    raw = m.group(1).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return json.loads(raw)


def parse_shapes(svg_path: Path):
    root = ET.fromstring(svg_path.read_text())
    ns = "{http://www.w3.org/2000/svg}"
    rects, segs, polys = [], [], []
    for el in root.iter():
        cls = el.get("class", "")
        if cls in ("grid", ""):
            continue
        tag = el.tag.replace(ns, "")
        if tag == "rect":
            rects.append({"cls": cls, "x": float(el.get("x")), "y": float(el.get("y")),
                          "w": float(el.get("width")), "h": float(el.get("height"))})
        elif tag == "image":
            rects.append({"cls": "shot", "x": float(el.get("x")), "y": float(el.get("y")),
                          "w": float(el.get("width")), "h": float(el.get("height"))})
        elif tag == "polygon":
            pts = [tuple(map(float, p.split(","))) for p in el.get("points").split()]
            polys.append({"cls": cls, "pts": pts})
            for a, b in zip(pts, pts[1:] + pts[:1]):
                segs.append({"cls": "shape-edge", "a": a, "b": b})
        elif tag == "path":
            pts = [tuple(map(float, p.split(",")))
                   for p in re.findall(r"(-?[\d.]+,-?[\d.]+)", el.get("d", ""))]
            for a, b in zip(pts, pts[1:]):
                segs.append({"cls": cls, "a": a, "b": b})
    return rects, segs, polys


def rect_of(d) -> tuple[float, float, float, float]:
    return d["x"], d["y"], d["x"] + d["w"], d["y"] + d["h"]


def overlap(a, b, pad: float = 0.0) -> bool:
    ax1, ay1, ax2, ay2 = rect_of(a)
    bx1, by1, bx2, by2 = rect_of(b)
    return not (ax2 + pad <= bx1 or bx2 + pad <= ax1 or ay2 + pad <= by1 or by2 + pad <= ay1)


def contains(outer, inner, pad: float = 0.0) -> bool:
    ox1, oy1, ox2, oy2 = rect_of(outer)
    ix1, iy1, ix2, iy2 = rect_of(inner)
    return ox1 - pad <= ix1 and oy1 - pad <= iy1 and ox2 + pad >= ix2 and oy2 + pad >= iy2


def gap(a, b) -> float:
    ax1, ay1, ax2, ay2 = rect_of(a)
    bx1, by1, bx2, by2 = rect_of(b)
    dx = max(bx1 - ax2, ax1 - bx2, 0.0)
    dy = max(by1 - ay2, ay1 - by2, 0.0)
    if dx == 0 and dy == 0:
        return 0.0
    return math.hypot(dx, dy)


def pt_seg_dist(p, a, b) -> float:
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg_dist(a1, a2, b1, b2) -> float:
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1, d2 = cross(b1, b2, a1), cross(b1, b2, a2)
    d3, d4 = cross(a1, a2, b1), cross(a1, a2, b2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg_dist(a1, b1, b2), pt_seg_dist(a2, b1, b2),
               pt_seg_dist(b1, a1, a2), pt_seg_dist(b2, a1, a2))


def seg_rect_dist(seg, r) -> float:
    x1, y1, x2, y2 = rect_of(r)
    a, b = seg["a"], seg["b"]
    inside = lambda p: x1 <= p[0] <= x2 and y1 <= p[1] <= y2
    if inside(a) or inside(b):
        return 0.0
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    return min(seg_seg_dist(a, b, corners[i], corners[(i + 1) % 4]) for i in range(4))


def check(svg_path: Path) -> tuple[list[str], list[str]]:
    texts = measure_text(svg_path)
    rects, segs, polys = parse_shapes(svg_path)
    root = ET.fromstring(svg_path.read_text())
    W, H = float(root.get("width")), float(root.get("height"))
    fails: list[str] = []
    warns: list[str] = []

    boxes = [r for r in rects if r["cls"] in ("box", "shot")]
    frames = [r for r in rects if r["cls"] == "frame"]
    edges = [s for s in segs if s["cls"] == "edge"]

    for t in texts:
        label = t["txt"][:34]
        x1, y1, x2, y2 = rect_of(t)
        if x1 < MARGIN or y1 < MARGIN or x2 > W - MARGIN or y2 > H - MARGIN:
            fails.append(f"BOUNDS text {label!r} at ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) "
                         f"breaks {MARGIN}px margin of {W:.0f}x{H:.0f}")
        for r in boxes + frames:
            if overlap(t, r) and not contains(r, t):
                fails.append(f"TEXT/BOX {label!r} crosses border of box at "
                             f"({r['x']:.0f},{r['y']:.0f},{r['w']:.0f}x{r['h']:.0f})")
            elif contains(r, t) and r["cls"] == "box":
                rx1, ry1, rx2, ry2 = rect_of(r)
                clear = min(x1 - rx1, ry1 and y1 - ry1, rx2 - x2, ry2 - y2)
                if clear < PAD_WARN:
                    warns.append(f"TIGHT {label!r} only {clear:.1f}px from its box edge")
        for s in edges:
            d = seg_rect_dist(s, t)
            if d < SEG_FAIL:
                fails.append(f"TEXT/ARROW {label!r} is {d:.1f}px from arrow segment "
                             f"{s['a']}-{s['b']}")
            elif d < SEG_WARN:
                warns.append(f"NEAR {label!r} is {d:.1f}px from an arrow segment")

    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if overlap(a, b):
                fails.append(f"TEXT/TEXT {a['txt'][:24]!r} overlaps {b['txt'][:24]!r}")
            elif overlap(a, b, pad=5) and gap(a, b) < 5:
                warns.append(f"CROWDED {a['txt'][:24]!r} and {b['txt'][:24]!r} "
                             f"only {gap(a, b):.1f}px apart")

    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if contains(a, b) or contains(b, a):
                continue
            g = gap(a, b)
            if overlap(a, b):
                fails.append(f"BOX/BOX overlap ({a['x']:.0f},{a['y']:.0f}) and "
                             f"({b['x']:.0f},{b['y']:.0f})")
            elif g < MIN_GAP:
                fails.append(f"BOX/BOX gap {g:.1f}px < {MIN_GAP} between "
                             f"({a['x']:.0f},{a['y']:.0f}) and ({b['x']:.0f},{b['y']:.0f})")

    for r in rects + [{"cls": "poly", "x": min(p[0] for p in q["pts"]),
                       "y": min(p[1] for p in q["pts"]),
                       "w": max(p[0] for p in q["pts"]) - min(p[0] for p in q["pts"]),
                       "h": max(p[1] for p in q["pts"]) - min(p[1] for p in q["pts"])}
                      for q in polys]:
        x1, y1, x2, y2 = rect_of(r)
        if x1 < MARGIN - 0.9 or y1 < MARGIN - 0.9 or x2 > W - MARGIN + 0.9 or y2 > H - MARGIN + 0.9:
            fails.append(f"BOUNDS shape {r['cls']} ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f})")

    for s in segs:
        for p in (s["a"], s["b"]):
            if not (MARGIN - 0.9 <= p[0] <= W - MARGIN + 0.9 and MARGIN - 0.9 <= p[1] <= H - MARGIN + 0.9):
                fails.append(f"BOUNDS arrow point {p}")

    for s in edges:
        for r in boxes:
            if seg_rect_dist(s, r) == 0.0:
                a, b = s["a"], s["b"]
                x1, y1, x2, y2 = rect_of(r)
                on_edge = all(
                    abs(p[0] - x1) < 1.2 or abs(p[0] - x2) < 1.2 or
                    abs(p[1] - y1) < 1.2 or abs(p[1] - y2) < 1.2
                    for p in (a, b) if x1 - 1.2 <= p[0] <= x2 + 1.2 and y1 - 1.2 <= p[1] <= y2 + 1.2
                )
                if not on_edge:
                    fails.append(f"ARROW/BOX segment {a}-{b} enters box "
                                 f"({r['x']:.0f},{r['y']:.0f},{r['w']:.0f}x{r['h']:.0f})")

    sizes = sorted({round(t["size"], 1) for t in texts})
    fams = sorted({t["family"].split(",")[0] for t in texts})
    warns.append(f"INFO font sizes in use: {sizes}; families: {fams}; "
                 f"{len(texts)} texts, {len(boxes)} boxes, {len(segs)} segments")
    return fails, warns


def main() -> None:
    svg_path = Path(sys.argv[1])
    root = ET.fromstring(svg_path.read_text())
    W, H = int(float(root.get("width"))), int(float(root.get("height")))
    png = svg_path.with_suffix(".png")
    render_png(svg_path, png, W, H)
    fails, warns = check(svg_path)
    print(f"== {svg_path.name}  {W}x{H}px  ->  {png.name} @{SCALE}x = {W*SCALE}x{H*SCALE}")
    for w in warns:
        print("  warn:", w)
    for f in fails:
        print("  FAIL:", f)
    print(f"  {len(fails)} failures, {len(warns) - 1} warnings")


if __name__ == "__main__":
    main()
