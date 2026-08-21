import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/Users/cooperkeenan/GitHub/CodeFlow")
sys.path.insert(0, str(ROOT/"scripts"))
from chrome_locator import ChromeLocator

src = (ROOT/"poster"/"poster.html").as_uri()
pdf = ROOT/"poster"/"poster.pdf"
png = ROOT/"poster"/"poster_preview.png"

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=ChromeLocator().find())
    pg = b.new_page(viewport={"width":3179,"height":2245}, device_scale_factor=1)
    pg.goto(src, wait_until="load")
    pg.wait_for_timeout(1500)
    pg.pdf(path=str(pdf), width="841mm", height="594mm", print_background=True,
           margin={"top":"0","right":"0","bottom":"0","left":"0"})
    pg.screenshot(path=str(png), full_page=True)
    # report any element rendering below the 16pt floor, and overflow
    info = pg.evaluate("""() => {
      const small = [];
      document.querySelectorAll('*').forEach(el => {
        if (!el.textContent.trim() || el.children.length) return;
        const fs = parseFloat(getComputedStyle(el).fontSize);
        if (fs < 16 * 96/72 - 0.5) small.push([Math.round(fs*72/96*10)/10, el.textContent.trim().slice(0,40)]);
      });
      const b = document.body;
      return {small: small.slice(0,15),
              scrollW: b.scrollWidth, clientW: b.clientWidth,
              scrollH: b.scrollHeight, clientH: b.clientHeight};
    }""")
    print(info)
    b.close()
for p in (pdf,png):
    print(p.name, p.stat().st_size if p.exists() else "MISSING")
