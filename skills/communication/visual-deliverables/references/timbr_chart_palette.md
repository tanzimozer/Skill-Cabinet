# TIMBR Chart Palette & Style Reference

## Colours
| Role                  | Hex        |
|-----------------------|------------|
| Background            | `#0A0A0F`  |
| Dark panel            | `#131318`  |
| Title / Gold          | `#C9A84C`  |
| Gold light            | `#E8C97A`  |
| Co-founder fill       | `#C9A84C` (text `#0A0A0F`) |
| Teal (infra/advisor)  | `#1B6B5F` / `#2A9E8E` |
| Blue (product)        | `#1A3A5C` / `#2A6A9E` |
| Purple (marketing)    | `#3A1F6B` / `#6A3FBB` |
| Red soft (trainers)   | `#6B1F1F`  |
| Slate (ops)           | `#1F2E3F`  |
| White text            | `#F0EDE8`  |
| Grey sub-label        | `#888888`  |
| Grey dim sub-label    | `#AAAAAA`  |

## Box Style
```python
FancyBboxPatch((x-w/2, y-h/2), w, h,
               boxstyle="round,pad=0.12",   # 0.15–0.18 for larger boxes
               linewidth=0,                  # or 1.2 for outlined boxes
               facecolor=color, edgecolor=ec)
```

## Arrow Style
```python
ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle='->', color=color, lw=1.6))
```

## Title Style
```python
ax.text(cx, y, 'Title Text', ha='center', fontsize=22, fontweight='bold',
        color='#C9A84C',
        path_effects=[pe.withStroke(linewidth=5, foreground='#0A0A0F')])
```

## DPI & Save
```python
plt.savefig('/tmp/filename.png', dpi=180, bbox_inches='tight', facecolor='#0A0A0F')
```

## Delivery
```bash
curl -s -X POST http://localhost:3000/send-media \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"chatId":"<id>","filePath":"/tmp/file.png","mediaType":"image","caption":"Caption"}'
```
Sleep 2s between sends.
