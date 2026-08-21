# A1 honours poster

`poster.pdf` is the deliverable: one page, 841 x 594 mm (**A1 landscape**), print-ready.

## Files

| File | What it is |
|---|---|
| `body.html` | The poster source. Edit this. Figures are placeholders (`<!--FIG1-->`, `<!--FIG4-->`, `HERO_B64`). |
| `build.py` | Inlines the two figure SVGs and the base64 screenshot into `poster.html`. |
| `render.py` | Renders `poster.html` to `poster.pdf` and `poster_preview.png` via headless Chrome. |
| `verify.py` | Layout checks: page overflow, clipped text, overlapping text, any type below 14.4 pt. |
| `harvest.md` | **Every number on the poster, with the command that produced it.** |
| `shot_decision_flow.png`, `shot_flowchart.png`, `shot_code_view.png` | Figures 3, 4 and 5 — all real django-helpdesk output. See `harvest.md` §8 for the exact crops. |
| `_hero_raw.png`, `_*_b64.txt`, `_fig*.svg` | Intermediates the build consumes. |

## Rebuild

```
python poster/build.py && python poster/render.py && python poster/verify.py
```

`verify.py` should report page height OK, 0 horizontal overflow, 0 below 14.4 pt and 0 overlaps.
The single `OVERSET: CodeFlow: Decision Flow Diagrams` line is the `h1` glyph box, not clipped text.

## Rule

No figure goes on the poster unless it traces to a block in `harvest.md`. Studies 7.2
(precision/recall vs a ground truth) and 7.3 (baseline comparison) have not been run, so the poster
makes no accuracy claim. If those numbers arrive, section 6 has room for a table.

Screenshots must be real analysis output. Several `scratch_out` captures show a synthetic
stress-test fixture (`method_0`, `value_0 = compute(...)`) — never use those.
