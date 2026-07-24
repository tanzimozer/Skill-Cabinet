# Interactive SVG Pipeline / Data-Flow Visualisations

When Tanzim is **thinking out loud / iterating on a concept** (not asking for a
final deliverable image), build an **interactive single-file HTML+SVG** he can open
in a browser and click through. This is different from the static PNG workflow in
SKILL.md — here the point is exploration, not a finished export.

Used this session to model the TIMBR thesis: fitness-money as a pipeline, segments
as nodes, a "valve" marking the bottleneck to own. Iterated fast from Seattle-map →
money-pipeline → PT-only in a few turns because it was one editable file.

## When to use this vs. static PNG

- **Interactive SVG (this file):** concept still moving, wants to click/inspect,
  expects several rebuilds. Deliver a `file://` path he opens himself.
- **Static PNG (SKILL.md):** finished chart to send/present, especially over WhatsApp.

## The pattern

- **One self-contained `.html`** — inline `<style>` + `<script>`, no build, no deps,
  no CDN. Opens from `file://`. Keeps iteration instant.
- **Data as a JS array at the top** — nodes/segments with `{id, name, x, y, <metric>,
  reason}` and a links array. Everything downstream derives from these, so a rebuild
  is just editing the array.
- **Encode two variables at once:** size (node radius / pipe width) = one metric
  (volume/flow), colour = a second metric (density/margin). Interpolate colour across
  a stop array in JS so the heatmap is continuous.
- **Click a node → side panel** shows its numbers + a one-line `reason`/`read`. The
  "why" per node is what makes it a thinking tool, not just a picture.
- **Mark the key insight visually** — e.g. a dashed gold "valve" ring + label on the
  bottleneck node. Draw attention to the one thing the whole diagram argues for.
- **Layout:** `grid-template-columns: 1fr <panel>px`, SVG left, panel right. Dark ops
  theme works well for exploration (`#070b12` bg, teal accent) — this is the *scratch*
  register, distinct from the white Apple deck aesthetic for final deliverables.
- **Fat invisible hit-area** — draw a transparent thick stroke over thin pipes so
  they're clickable; thin visible lines are hard to hit.
- **Verify via browser:** `browser_navigate` to the `file://` path then `browser_vision`
  to confirm it renders coherently before handing over.

## Register

- Numbers are usually **modelled placeholders** early. Say so plainly, every time —
  Tanzim wants nothing looking like verified fact before it's checked. Offer to wire
  real data once the shape is agreed.
- Scratch work goes in `~/scratch/<project>/` — no repo until the idea earns one
  (his explicit preference: prove it locally first).
