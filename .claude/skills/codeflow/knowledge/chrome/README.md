# Chrome / Browser Automation

Notes on driving a real browser from Claude Code via the Claude in Chrome extension.

## Setup

- `/chrome` writes the native messaging host key, then Chrome must be **fully restarted** — it reads
  that key only at startup. Then `/chrome` → Reconnect extension.
- Required state before browser tools work: **Status: Enabled** and **Extension: Installed**.
- If Chrome integration refuses to enable, the session is API-key/token authed rather than `/login`
  authed, and browser tools are unavailable by design.
- Site permissions must be granted per-domain in the extension before tools will act on that domain.

## 2026-09-22 — Multiple browsers can be connected at once

`list_connected_browsers` returned two: a macOS Chrome and a Windows Chrome, both signed into the
same account. When more than one is connected and none is selected, **every** browser tool refuses
until `select_browser` is called with a deviceId.

Consequence worth remembering: **the browser and the shell can be on different machines.** A Claude
Code session running on the Mac can drive Chrome on the Windows box, but its Bash tool still runs on
the Mac. Do not assume a browser observation and a shell command share a filesystem or a git
checkout.

## 2026-09-22 — The Microsoft account-picker identity trap

Signing into `aex.dev.azure.com` lands on `login.microsoftonline.com` with a "Pick an account" list.
The picker is **not** a reliable way to tell a personal Microsoft Account from an Entra work account
when both carry the same address:

- Rows that have an active session show a display name and "Signed in".
- A row with **no session shows only the bare address** — no display name, no account-type hint.

So `cooper@skych.uk` appearing in the list says nothing about whether clicking it resolves to the
work account or the federated MSA. An alias on the MSA (`cooper.keenan401@outlook.com`) is the
disambiguator, but **the alias is not shown in the picker** — it only helps once you are past it.

**Rule:** before acting in a Microsoft property, open the account menu / user pill and read the
actual UPN. Do not infer identity from the sign-in picker.

## Gotchas

- **Never trigger `alert`/`confirm`/`prompt` or any modal dialog.** They block the extension from
  receiving further commands and the session goes unresponsive until a human dismisses it manually.
  Use `console.log` plus `read_console_messages` instead.
- Use the `pattern` argument on `read_console_messages` to filter; raw console output is verbose.
- Prefer `browser_batch` for sequences of clicks/types/navigations — far faster than one call each.
- Create a new tab per conversation rather than reusing an existing one, and close tabs you opened.
- The MCP server can disconnect mid-session; its tools then vanish from the tool list and the browser
  work has to pause until it reconnects.

## Related — this repo's own browser tooling

`scripts/flow_agent.py` drives the real `FlowPage` with Playwright (installed Chrome via
`channel="chrome"`, no browser download) and reports the page **as text** so state can be asserted.
That is unrelated to the Chrome extension and is the correct tool for testing CodeFlow's frontend —
see `reference/tooling.md`.

## 2026-10-01 — Screenshots are downscaled at browser zoom; measure in the page instead

On the user's MacBook, Chrome ran at ~110% zoom (`devicePixelRatio` 2.2, `innerWidth` 1527). The
`computer` screenshot came back at 1375×713 in a 1512×785 coordinate frame. The controls bar looked
cut off at the right edge and the composer looked pushed off the bottom, but neither was true.
`javascript_tool` showed every element inside `innerWidth`/`innerHeight`. Before dispatching a
layout fix from a screenshot, measure with `getBoundingClientRect()` against
`innerWidth`/`innerHeight` in the page.

## 2026-10-01 — Clicking straight after `navigate` can miss

A click on a centred empty-state button right after `navigate` focused it but didn't fire, or landed
on a different button after a layout shift. Wait ~2s, or use `find` → click by `ref` (that worked
reliably for the composer textarea), then `type` + `Return`.

## 2026-10-01 — Harness "instant mode" hides animation bugs

A harness that disables animation for deterministic screenshots can't see bugs that exist only
while animating. In Brainstorm, a CSS `transform` keyframe overrode an SVG `transform` attribute and
detached a bubble from its text. That was visible only in live playback in the real browser. After
any change involving motion, drive the real page with animation on.
