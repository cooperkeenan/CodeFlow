from __future__ import annotations

from dataclasses import dataclass, field
from PIL import ImageFont

HELV = "/System/Library/Fonts/Helvetica.ttc"
COUR = "/System/Library/Fonts/Courier.ttc"

FONT_STACK = "Helvetica, Arial, sans-serif"
MONO_STACK = "Courier, monospace"

BODY = 13
SEC = 11
LINE_H = 16
MONO_LH = 17

STROKE_W = 1.6
RADIUS = 4
EDGE_COLOR = "#4d4d4d"
DASH = "5 4"

PALETTE = {
    "white": ("#ffffff", "#4d4d4d"),
    "blue": ("#dae8fc", "#6c8ebf"),
    "green": ("#d5e8d4", "#82b366"),
    "amber": ("#ffe6cc", "#d79b00"),
    "grey": ("#f5f5f5", "#999999"),
    "panel": ("#ffffff", "#b3b3b3"),
}

_cache: dict[tuple, ImageFont.FreeTypeFont] = {}


def _font(size: int, bold: bool, mono: bool) -> ImageFont.FreeTypeFont:
    key = (size, bold, mono)
    if key not in _cache:
        path, idx = (COUR, 1 if bold else 0) if mono else (HELV, 1 if bold else 0)
        _cache[key] = ImageFont.truetype(path, size, index=idx)
    return _cache[key]


def measure(text: str, size: int = BODY, bold: bool = False, mono: bool = False) -> float:
    return _font(size, bold, mono).getlength(text)


def wrap(text: str, max_w: float, size: int = BODY, bold: bool = False) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if cur and measure(trial, size, bold) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def box_width_for(labels: list[tuple[str, int, bool]], pad: float = 14) -> float:
    return max(measure(t, s, b) for t, s, b in labels) + 2 * pad


@dataclass
class Line:
    text: str
    size: int = BODY
    bold: bool = False
    fill: str = "#000000"


@dataclass
class Svg:
    width: float
    height: float
    parts: list[str] = field(default_factory=list)

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(
        self,
        x: float,
        y: float,
        s: str,
        size: int = BODY,
        bold: bool = False,
        anchor: str = "middle",
        fill: str = "#000000",
        mono: bool = False,
        cls: str = "label",
    ) -> None:
        stack = MONO_STACK if mono else FONT_STACK
        weight = ' font-weight="bold"' if bold else ""
        esc = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.add(
            f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" font-family="{stack}" '
            f'font-size="{size}"{weight} fill="{fill}" text-anchor="{anchor}" '
            f'xml:space="preserve">{esc}</text>'
        )

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: str = "white",
        cls: str = "box",
        dashed: bool = False,
        radius: float = RADIUS,
    ) -> None:
        fill, stroke = PALETTE[color]
        d = f' stroke-dasharray="{DASH}"' if dashed else ""
        self.add(
            f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{radius}" ry="{radius}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{STROKE_W}"{d}/>'
        )

    def labelled_box(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        lines: list[Line],
        color: str = "white",
        cls: str = "box",
    ) -> None:
        self.rect(x, y, w, h, color, cls)
        self.stack_text(x + w / 2, y + h / 2, lines)

    def stack_text(self, cx: float, cy: float, lines: list[Line], anchor: str = "middle") -> None:
        n = len(lines)
        block = (n - 1) * LINE_H
        first = cy - block / 2
        for i, ln in enumerate(lines):
            baseline = first + i * LINE_H + 0.36 * ln.size
            self.text(cx, baseline, ln.text, ln.size, ln.bold, anchor, ln.fill)

    def path(
        self,
        pts: list[tuple[float, float]],
        arrow: bool = True,
        dashed: bool = False,
        cls: str = "edge",
    ) -> None:
        d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        m = ' marker-end="url(#arrowhead)"' if arrow else ""
        da = f' stroke-dasharray="{DASH}"' if dashed else ""
        self.add(
            f'<path class="{cls}" d="{d}" fill="none" stroke="{EDGE_COLOR}" '
            f'stroke-width="{STROKE_W}" stroke-linejoin="round"{da}{m}/>'
        )

    def polygon(self, pts: list[tuple[float, float]], color: str = "green", cls: str = "box") -> None:
        fill, stroke = PALETTE[color]
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(
            f'<polygon class="{cls}" points="{p}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{STROKE_W}" stroke-linejoin="round"/>'
        )

    def image(self, x: float, y: float, w: float, h: float, href: str, cls: str = "shot") -> None:
        self.add(
            f'<image class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'href="{href}" preserveAspectRatio="xMidYMid meet"/>'
        )

    def render(self) -> str:
        defs = f"""<defs>
<pattern id="minorGrid" width="10" height="10" patternUnits="userSpaceOnUse">
<path d="M 10 0 L 0 0 L 0 10" fill="none" stroke="#e8e8e8" stroke-width="1"/>
</pattern>
<pattern id="majorGrid" width="100" height="100" patternUnits="userSpaceOnUse">
<rect width="100" height="100" fill="url(#minorGrid)"/>
<path d="M 100 0 L 0 0 L 0 100" fill="none" stroke="#d5d5d5" stroke-width="1.4"/>
</pattern>
<marker id="arrowhead" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="8"
 refX="10.5" refY="4" orient="auto">
<path d="M 0 0 L 10.5 4 L 0 8 z" fill="{EDGE_COLOR}"/>
</marker>
</defs>"""
        body = "\n".join(self.parts)
        return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
 width="{self.width:.0f}" height="{self.height:.0f}"
 viewBox="0 0 {self.width:.0f} {self.height:.0f}">
{defs}
<rect class="grid" x="0" y="0" width="{self.width:.0f}" height="{self.height:.0f}" fill="#ffffff"/>
<rect class="grid" x="0" y="0" width="{self.width:.0f}" height="{self.height:.0f}" fill="url(#majorGrid)"/>
{body}
</svg>
"""

    def save(self, path: str) -> None:
        with open(path, "w") as fh:
            fh.write(self.render())
