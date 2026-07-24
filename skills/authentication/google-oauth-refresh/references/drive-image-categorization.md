# Google Drive Image Categorization by Content Type

Bulk sort images from Drive folders into category folders using vision AI.

## Pattern: Vision-Based Image Sorting

### 1. Create Category Folders
```python
import json, urllib.request, urllib.parse

PARENT_FOLDER_ID = "..."  # folder containing source batches
pattern_folders = [
    "Fitness & Workout",
    "Screenshots - Apps & UI",
    "Screenshots - Chat & Messages",
    "Screenshots - Receipts & Confirmations",
    "Personal Photos - Selfies & Portraits",
    "Personal Photos - Travel & Outdoors",
    "Documents & Scans",
    "Social Media Content",
    "Food & Products",
    "Memes & Graphics",
    "Contact Spreadsheets",
    "Project Files - Blair",
    "Videos",
    "Uncategorized"
]

created = {}
for name in pattern_folders:
    data = json.dumps({
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [PARENT_FOLDER_ID]
    }).encode()
    req = urllib.request.Request(
        'https://www.googleapis.com/drive/v3/files?fields=id,name',
        data=data,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    result = json.loads(urllib.request.urlopen(req).read())
    created[name] = result['id']
```

### 2. Vision Categorization Prompt
```python
prompt = """Categorize this image into ONE of these categories:

1. fitness - Workout plans, gym photos, exercise demonstrations
2. screenshots_app - App interfaces, settings, menus, login screens
3. screenshots_chat - Text messages, WhatsApp, iMessage, DMs
4. screenshots_receipt - Payment confirmations, order receipts
5. photos_selfie - Selfies, portraits, couple photos, group photos
6. photos_travel - Landscapes, beaches, mountains, travel destinations
7. documents - Scanned documents, handwritten notes, forms
8. social_media - Instagram posts, Twitter/X posts, social profiles
9. food_products - Food photos, product shots, items for sale
10. memes_graphics - Memes, motivational quotes, graphic designs
11. contact_sheets - Spreadsheets with contact info (names, phones, emails)
12. uncategorized - Anything that doesn't fit above

Reply with ONLY the category name. Nothing else."""
```

### 3. File-based Pre-categorization (No Vision)
```python
def categorize_by_filename(filename):
    name_lower = filename.lower()
    
    # Videos - no vision needed
    if name_lower.endswith(('.mov', '.mp4', '.m4v', '.avi')):
        return "videos"
    
    # Known project files
    if 'blair' in name_lower:
        return "blair_project"
    
    # PhotoRoom edits (product photos)
    if 'photoroom' in name_lower:
        return "food_products"
    
    return None  # Need vision
```

### 4. Move File to Category Folder
```python
def move_file(file_id, dest_folder_id, token):
    # Get current parents
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}?fields=parents',
        headers={'Authorization': f'Bearer {token}'}
    )
    result = json.loads(urllib.request.urlopen(req).read())
    current_parents = ','.join(result.get('parents', []))
    
    # Move to new folder
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}?addParents={dest_folder_id}&removeParents={current_parents}&fields=id',
        method='PATCH',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        data=b'{}'
    )
    urllib.request.urlopen(req)
```

## Performance Notes

- **Parallel processing**: Deploy 4 agents for 4 source folders simultaneously
- **Rate limiting**: Add `time.sleep(0.2)` between API calls
- **Skip large files**: Images >5MB often fail vision API; categorize as uncategorized
- **Use Haiku for bulk**: `claude-haiku-4-5` with OAuth token is fast/cheap for categorization

## Typical Category Distribution (from 1800 image sample)

| Category | % |
|----------|---|
| Videos (.mov/.mp4) | ~25% |
| IMG_ numbered photos | ~80% of images |
| UUID-style names | ~8% |
| Screenshots | ~15% |
| Personal photos | ~30% |
| Fitness content | ~10% |
| Documents | ~5% |
| Social media | ~5% |
| Project files | ~2% |

## Quality Check After Categorization

Run this after all batches complete to verify categorization worked:

```python
# List pattern folders and count files
parent_id = "..."  # Parent folder ID
url = f"https://www.googleapis.com/drive/v3/files?q='{parent_id}'+in+parents+and+mimeType='application/vnd.google-apps.folder'+and+trashed=false&fields=files(id,name)&pageSize=100"
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
folders = json.loads(urllib.request.urlopen(req).read()).get('files', [])

total = 0
for f in sorted(folders, key=lambda x: x['name']):
    count_url = f"https://www.googleapis.com/drive/v3/files?q='{f['id']}'+in+parents+and+trashed=false&fields=files(id)&pageSize=1000"
    count = len(json.loads(urllib.request.urlopen(
        urllib.request.Request(count_url, headers={'Authorization': f'Bearer {token}'})
    ).read()).get('files', []))
    total += count
    if count > 0:
        print(f"📁 {f['name']}: {count} files")

print(f"\nTOTAL: {total} files categorized")
```

**Quality metrics:**
- Uncategorized rate should be <5% (target: 3%)
- Error rate should be 0% (vision failures → uncategorized)
- Compare total against batch log totals to verify no files lost
