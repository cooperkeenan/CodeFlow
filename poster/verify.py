import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path("/Users/cooperkeenan/GitHub/CodeFlow"); sys.path.insert(0, str(ROOT/"scripts"))
from chrome_locator import ChromeLocator

JS = r"""() => {
  const PX_PER_PT = 96/72;
  const out = {small:[], overflowX:0, clipped:[], overlaps:[], count:0};
  const body = document.body;
  out.overflowX = body.scrollWidth - body.clientWidth;
  out.pageH = body.clientHeight; out.contentH = body.scrollHeight;
  const leaves = [...document.querySelectorAll('body *')].filter(el =>
      !el.closest('svg') && el.textContent.trim() && ![...el.children].some(c=>c.textContent.trim()));
  out.count = leaves.length;
  const boxes = [];
  for (const el of leaves) {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const pt = parseFloat(cs.fontSize)/PX_PER_PT;
    if (pt < 14.4) out.small.push([Math.round(pt*10)/10, el.textContent.trim().slice(0,45)]);
    if (r.bottom > body.clientHeight + 1 || r.right > body.clientWidth + 1 || r.left < -1)
      out.clipped.push([el.textContent.trim().slice(0,45), Math.round(r.right), Math.round(r.bottom)]);
    if (el.scrollHeight > el.clientHeight + 2 && cs.overflow === 'visible' && el.clientHeight > 0)
      out.clipped.push(['OVERSET: '+el.textContent.trim().slice(0,35), 0, 0]);
    boxes.push([r, el.textContent.trim().slice(0,30)]);
  }
  for (let i=0;i<boxes.length;i++) for (let j=i+1;j<boxes.length;j++){
    const [a,ta]=boxes[i],[b,tb]=boxes[j];
    const ox = Math.min(a.right,b.right)-Math.max(a.left,b.left);
    const oy = Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
    if (ox > 3 && oy > 3) out.overlaps.push([ta,tb,Math.round(ox),Math.round(oy)]);
  }
  return out;
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=ChromeLocator().find())
    pg = b.new_page(viewport={"width":3179,"height":2245})
    pg.goto((ROOT/"poster"/"poster.html").as_uri(), wait_until="load"); pg.wait_for_timeout(1200)
    r = pg.evaluate(JS); b.close()

print(f"text elements checked : {r['count']}")
print(f"page height           : {r['pageH']}px   content: {r['contentH']}px   "
      f"{'OK' if r['contentH']<=r['pageH'] else 'OVERFLOW '+str(r['contentH']-r['pageH'])+'px'}")
print(f"horizontal overflow   : {r['overflowX']}px {'OK' if r['overflowX']<=0 else 'FAIL'}")
print(f"below 14.4pt          : {len(r['small'])} {r['small'][:6]}")
print(f"clipped / overset     : {len(r['clipped'])} {r['clipped'][:6]}")
print(f"overlapping text      : {len(r['overlaps'])} {r['overlaps'][:4]}")
