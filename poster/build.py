from pathlib import Path

P = Path(__file__).resolve().parent
html = (P / "body.html").read_text()
for token, src in [
    ("<!--FIG1-->", P / "_fig1_architecture.svg"),
    ("<!--FIG4-->", P / "_fig4_significance_filter.svg"),
]:
    html = html.replace(token, src.read_text())
for token, src in [
    ("HERO_B64", P / "_hero_b64.txt"),
    ("D3_B64", P / "_d3_b64.txt"),
    ("FLOWCHART_B64", P / "_flowchart_b64.txt"),
]:
    html = html.replace(token, src.read_text().strip())
(P / "poster.html").write_text(html)
print("poster.html", len(html), "bytes")
