# Doc-style / visual tabs — section bands, snapshot-friendly

## When
A tab holds prose/plan content (stage descriptions, engineering plans, open questions) crammed as bullet lines in column A — a wall of text. User asks to make it "more visual / easy to read / easy to snapshot the data." Rebuild presentation only; **never change the actual content/wording** unless asked.

## Layout anatomy
- **Title bar** (row 1): dark fill, white bold ~18pt, merged across all cols, ~48px tall, left-padded.
- **Subtitle strip** (row 2): light fill, italic ~11pt summary, merged, wrapped.
- **Section bands**: one merged coloured bar per section (I/O, Engineering, Product, Config, Open Questions). White bold text on a distinct colour per section. ~32px.
- **Body rows**: content in a white "card" merged across the content columns (e.g. C:F), wrapped, padded, ~10pt. Optional **tag chip** in column B (coloured cell, e.g. IN / OUT) matching the section colour.
- **Spacer rows** (~10px) between sections for breathing room.
- **Gridlines off** for the whole tab — reads like a document.
- **Column layout**: A = thin gutter (~34px), B = tag chip (~84px), C = wide content (~560px), D–F = thin gutters merged into content.

## Colour palette used (hex)
- Title fill `#1f3a5f` (navy), text white
- Subtitle fill `#eaf0f6`, text `#33475b`
- Sections: I/O `#2a9d8f` (teal) · Engineering `#3d5a80` (blue) · Product `#588157` (green) · Config `#6c757d` (grey) · Open Questions `#bc6c25` (amber)
- Body card white `#ffffff`, text `#1f2933`

## Builder skeleton
```python
def rgb(h):
    h=h.lstrip('#'); return {"red":int(h[0:2],16)/255,"green":int(h[2:4],16)/255,"blue":int(h[4:6],16)/255}

NCOLS=6
# 1) sections = [(name, color_key, [(tag, body), ...]), ...]
# 2) Build a value matrix + a parallel `roles` list:
#    ('title'),('sub'),('spacer'),('sec',key),('body',key,has_tag)
# 3) Ensure grid: updateSheetProperties gridProperties rowCount/columnCount >= needed
# 4) values().clear() the tab, then unmergeCells over the whole range
# 5) values().update() write the matrix
# 6) Loop roles -> emit mergeCells + repeatCell(format) + updateDimensionProperties(row height) per row
# 7) Append {'updateSheetProperties': gridProperties.hideGridlines=True}
# 8) One batchUpdate with all requests
```

## Sequence pitfalls (learned the hard way)
- **Two passes**: write values first (a separate `values().update`), THEN the formatting `batchUpdate`. Mixing merges with value writes in one shot fights itself.
- **Unmerge before re-merge** — an old merged range that overlaps a new merge throws an error. `unmergeCells` over the full range first.
- **Expand the grid before writing wide** — see the grid-cap pitfall in SKILL.md.
- **Verify visually if you can** — browser screenshot of the live sheet needs a Google login session; in a headless/no-login env it'll time out. Fall back to describing the before/after to the user and sending the gid link.
- **Roll one tab as a prototype, get a thumbs-up, then batch the rest** — don't redesign 7 tabs blind. Build one, show the user the link, replicate on approval.

## Replication
Once the user approves the prototype, apply the identical builder to sibling tabs (Filter, Store, Enrich, Output, Follow, Schedule) — same palette, same role structure, only the section content differs.
