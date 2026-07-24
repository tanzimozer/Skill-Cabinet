#!/usr/bin/env python3
"""
Scan one Google Drive folder for spreadsheet contact screenshots.
Target: Excel/Sheets screenshots with 3+ rows, each row has name + phone + email.
Copy matches to destination folder.
Usage: python3 final_scan.py <SOURCE_FOLDER_ID> <FOLDER_LABEL> <DEST_FOLDER_ID>
"""

import json, urllib.request, urllib.parse, os, sys, time, base64, re, subprocess, tempfile

TOKEN_PATH = os.path.expanduser('~/.hermes/google_token.json')
CLIENT_SECRET_PATH = os.path.expanduser('~/.hermes/google_client_secret.json')

def refresh_gdrive():
    with open(TOKEN_PATH) as f: tok = json.load(f)
    with open(CLIENT_SECRET_PATH) as f: sec = json.load(f)
    web = sec.get('web') or sec.get('installed', {})
    data = urllib.parse.urlencode({
        'client_id': tok.get('client_id') or web['client_id'],
        'client_secret': tok.get('client_secret') or web['client_secret'],
        'refresh_token': tok['refresh_token'], 'grant_type': 'refresh_token'
    }).encode()
    resp = json.loads(urllib.request.urlopen(
        urllib.request.Request('https://oauth2.googleapis.com/token', data=data, method='POST')
    ).read())
    tok['token'] = resp['access_token']
    with open(TOKEN_PATH, 'w') as f: json.dump(tok, f)
    return resp['access_token']

def get_anthropic_key():
    with open(os.path.expanduser('~/.hermes/.env')) as f:
        for line in f:
            line = line.strip()
            if line.startswith('CLAUDE_CODE_OAUTH_TOKEN='):
                return line.split('=',1)[1].strip().strip('"').strip("'")

def list_all_images(folder_id, token):
    images, page_token = [], None
    while True:
        q = urllib.parse.quote(f"'{folder_id}' in parents and trashed = false")
        url = f'https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name,mimeType)&pageSize=200'
        if page_token: url += f'&pageToken={page_token}'
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        result = json.loads(urllib.request.urlopen(req).read())
        images.extend([f for f in result.get('files',[]) if f.get('mimeType','').startswith('image/')])
        page_token = result.get('nextPageToken')
        if not page_token: break
    return images

def download_image(file_id, token):
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media',
        headers={'Authorization': f'Bearer {token}'}
    )
    return urllib.request.urlopen(req, timeout=30).read(4*1024*1024)

def ocr_gate(image_bytes):
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(image_bytes); tmp = f.name
    try:
        r = subprocess.run(['tesseract', tmp, 'stdout', '--psm', '6'],
                           capture_output=True, text=True, timeout=20)
        text = r.stdout
    except: text = ""
    finally: os.unlink(tmp)
    emails = len(re.findall(r'\b\S+@\S+\.\S+\b', text))
    phones = len(re.findall(r'\d{3}[-.\s]\d{3}[-.\s]\d{4}', text))
    return emails, phones

def vision_check(image_bytes, filename, api_key):
    ext = filename.lower().split('.')[-1]
    mt = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png'}.get(ext,'image/jpeg')
    b64 = base64.standard_b64encode(image_bytes).decode()
    payload = json.dumps({
        "model": "claude-haiku-4-5", "max_tokens": 5,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mt, "data": b64}},
            {"type": "text", "text": "Is this a spreadsheet with 3+ rows each containing a person name, phone number, and email address? YES or NO only."}
        ]}]
    }).encode()
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages', data=payload,
        headers={'Authorization': f'Bearer {api_key}', 'anthropic-version': '2023-06-01',
                 'content-type': 'application/json'}
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        return resp['content'][0]['text'].strip()
    except Exception as e:
        return f"ERROR:{e}"

def copy_to_folder(file_id, dest_folder_id, token):
    data = json.dumps({'parents': [dest_folder_id]}).encode()
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{file_id}/copy?fields=id,name',
        data=data,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    try:
        result = json.loads(urllib.request.urlopen(req).read())
        return True, result.get('name','')
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 final_scan.py <SOURCE_FOLDER_ID> <LABEL> <DEST_FOLDER_ID>")
        sys.exit(1)

    folder_id, label, dest_id = sys.argv[1], sys.argv[2], sys.argv[3]
    log_file = f"/tmp/final_scan_{label}.txt"

    print(f"=== Scanning: {label} ===")
    gdrive_token = refresh_gdrive()
    api_key = get_anthropic_key()
    images = list_all_images(folder_id, gdrive_token)
    print(f"📊 {len(images)} images\n")

    total = len(images)
    ocr_rejected = vision_rejected = 0
    matched = []; errors = []

    with open(log_file, 'w') as log:
        log.write(f"Folder: {label}\nTotal: {total}\n\n")
        for i, img in enumerate(images, 1):
            print(f"[{i}/{total}] {img['name']}")
            log.write(f"[{i}/{total}] {img['name']}\n")
            try:
                img_bytes = download_image(img['id'], gdrive_token)
                emails, phones = ocr_gate(img_bytes)
                if emails < 2 and phones < 2:
                    result = f"  OCR REJECT (em={emails} ph={phones})"
                    ocr_rejected += 1
                else:
                    answer = vision_check(img_bytes, img['name'], api_key)
                    if answer.upper().startswith('YES') and 'ERROR' not in answer:
                        ok, name = copy_to_folder(img['id'], dest_id, gdrive_token)
                        result = f"  ✅ MATCH — copied" if ok else f"  ⚠️ COPY FAIL: {name}"
                        if ok: matched.append(img['name'])
                        else: errors.append(img['name'])
                    else:
                        result = f"  vision: {answer[:60]}"
                        vision_rejected += 1
            except Exception as e:
                result = f"  ⚠️ ERROR: {e}"
                errors.append(img['name'])
            print(result); log.write(result + '\n'); log.flush()
            if i % 100 == 0:
                print(f"\n--- {i}/{total} done | {len(matched)} matches ---\n")
            time.sleep(0.3)

    summary = f"\n{'='*50}\n{label}: scanned={total} ocr_rejected={ocr_rejected} vision_rejected={vision_rejected} matched={len(matched)} errors={len(errors)}\n"
    summary += '\n'.join(f"  ✅ {f}" for f in matched)
    print(summary)
    with open(log_file, 'a') as log: log.write(summary)

if __name__ == '__main__':
    main()
