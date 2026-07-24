"""
iCloud to Google Drive pipeline v2 — parallel uploads, resume support.
Verified working: 2026-05-31.

Processed:
  - iCloud to Google - 1: 1004 files (872 Photos, 132 Videos)
  - iCloud to Google - 2: 1008 files
  - iCloud to Google - 4: 336 files (196 Photos, 140 Videos)
  - iCloud to Google - 3: SKIPPED (18.8GB, insufficient disk after 1+2)

Parent folder on Drive: 18-3ya4x6q_sB2rqg0fdbdZdOcKgL96dW
"""

import json, os, sys, time, shutil, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '/home/hermes/.hermes/hermes-agent/venv/lib/python3.11/site-packages')

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

LOG = '/home/hermes/icloud_pipeline.log'
WORK_DIR = '/home/hermes/icloud_work'
PARENT_FOLDER_ID = '18-3ya4x6q_sB2rqg0fdbdZdOcKgL96dW'
UPLOAD_THREADS = 8

# Add/remove zips as needed. Set already_extracted=True + drive_folder_id if resuming.
ZIPS = [
    {'name': 'iCloud to Google - 1', 'zip_id': '1Czz2gx6ifACMq591p-nvmMvuUvRLKfxk', 'size_gb': 7.0},
    {'name': 'iCloud to Google - 2', 'zip_id': '1mk1QWTw8hNPuiq_ZgktgzTdbqkXSmrvF', 'size_gb': 5.8},
    {'name': 'iCloud to Google - 3', 'zip_id': '1jAX-6N_E913FqXAEEi89hJBWiYvm9ukf', 'size_gb': 18.8},
    {'name': 'iCloud to Google - 4', 'zip_id': '1U7pmLIzM6656ihnT96jXOFucvM53vlLz', 'size_gb': 12.1},
]

log_lock = threading.Lock()

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    with log_lock:
        print(line, flush=True)
        with open(LOG, 'a') as f:
            f.write(line + '\n')

def get_creds():
    with open('/home/hermes/.hermes/google_token.json') as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes')
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def get_drive():
    return build('drive', 'v3', credentials=get_creds())

def get_already_uploaded(drive, folder_id):
    uploaded = set()
    page_token = None
    while True:
        resp = drive.files().list(
            q=f"'{folder_id}' in parents",
            pageSize=1000,
            fields="nextPageToken, files(name)",
            pageToken=page_token
        ).execute()
        for f in resp.get('files', []):
            uploaded.add(f['name'])
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return uploaded

def create_drive_folder(drive, name, parent_id):
    meta = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    folder = drive.files().create(body=meta, fields='id,webViewLink').execute()
    return folder['id'], folder['webViewLink']

def download_zip(drive, file_id, dest_path, label):
    request = drive.files().get_media(fileId=file_id)
    with open(dest_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=100*1024*1024)
        done = False
        last_pct = 0
        while not done:
            status, done = downloader.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                if pct >= last_pct + 10:
                    log(f"  [{label}] Download: {pct}%")
                    last_pct = pct

def upload_single(args):
    fpath, fname, folder_id = args
    ext = fname.lower().rsplit('.', 1)[-1] if '.' in fname else ''
    mime_map = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'gif': 'image/gif', 'heic': 'image/heic', 'heif': 'image/heif',
        'mp4': 'video/mp4', 'mov': 'video/quicktime', 'avi': 'video/avi',
        'm4v': 'video/mp4', '3gp': 'video/3gpp',
        'aae': 'application/octet-stream', 'json': 'application/json',
    }
    mime = mime_map.get(ext, 'application/octet-stream')
    try:
        drive = get_drive()  # fresh per thread — Drive clients not thread-safe
        meta = {'name': fname, 'parents': [folder_id]}
        media = MediaFileUpload(fpath, mimetype=mime, resumable=True, chunksize=5*1024*1024)
        req = drive.files().create(body=meta, media_body=media, fields='id')
        response = None
        while response is None:
            _, response = req.next_chunk()
        return ('ok', fname)
    except Exception as e:
        return ('err', fname, str(e))

def categorize(fname):
    ext = fname.lower().rsplit('.', 1)[-1] if '.' in fname else 'unknown'
    if ext in ('jpg', 'jpeg', 'png', 'gif', 'heic', 'heif', 'bmp', 'tiff', 'webp', 'raw'):
        return 'Photos'
    elif ext in ('mp4', 'mov', 'avi', 'mkv', 'm4v', '3gp', 'm4p'):
        return 'Videos'
    elif ext == 'aae':
        return 'iOS Metadata'
    elif ext == 'json':
        return 'Metadata JSON'
    else:
        return f'Other ({ext})'

def process_zip(z):
    name = z['name']
    log(f"=== Starting: {name} ===")

    work = Path(WORK_DIR) / name
    extract_dir = work / 'extracted'

    if not z.get('already_extracted'):
        stat = shutil.disk_usage('/home/hermes')
        free_gb = stat.free / 1e9
        log(f"Disk free: {free_gb:.1f} GB (need ~{z['size_gb']*2.5:.0f} GB)")
        if free_gb < z['size_gb'] * 2.5:
            log(f"ERROR: Not enough disk. Skipping {name}.")
            return None

        work.mkdir(parents=True, exist_ok=True)
        extract_dir.mkdir(parents=True, exist_ok=True)
        zip_path = work / f"{name}.zip"

        log(f"Downloading {name}.zip ({z['size_gb']} GB)...")
        drive = get_drive()
        download_zip(drive, z['zip_id'], str(zip_path), name)
        log("Downloaded. Unzipping...")

        import zipfile
        try:
            with zipfile.ZipFile(str(zip_path), 'r') as zf:
                members = zf.namelist()
                log(f"Zip has {len(members)} entries")
                zf.extractall(str(extract_dir))
        except Exception as e:
            log(f"zipfile error: {e} — falling back to system unzip")
            os.system(f'unzip -q "{zip_path}" -d "{extract_dir}"')

        os.remove(str(zip_path))
        log("Zip deleted locally.")

        drive = get_drive()
        folder_id, folder_url = create_drive_folder(drive, name, PARENT_FOLDER_ID)
        log(f"Drive folder created: {folder_url}")
    else:
        folder_id = z['drive_folder_id']
        folder_url = z['drive_folder_url']
        log(f"Resuming. Drive folder: {folder_url}")

    # Collect files
    all_files = []
    for root, dirs, files in os.walk(str(extract_dir)):
        for fname in files:
            if not fname.startswith('._') and fname not in ('.DS_Store',):
                all_files.append((os.path.join(root, fname), fname))

    log(f"Total files: {len(all_files)}")

    drive = get_drive()
    already = get_already_uploaded(drive, folder_id)
    log(f"Already uploaded: {len(already)} — skipping")

    to_upload = []
    categories = {}
    skipped_meta = 0

    for fpath, fname in all_files:
        cat = categorize(fname)
        categories[cat] = categories.get(cat, 0) + 1
        if cat == 'iOS Metadata':
            skipped_meta += 1
            continue
        if fname in already:
            continue
        to_upload.append((fpath, fname, folder_id))

    log(f"To upload: {len(to_upload)} ({skipped_meta} iOS metadata skipped, {len(already)} already done)")
    log(f"Breakdown: {json.dumps(categories)}")

    uploaded = 0
    errors = 0
    total = len(to_upload)

    with ThreadPoolExecutor(max_workers=UPLOAD_THREADS) as executor:
        futures = {executor.submit(upload_single, args): args[1] for args in to_upload}
        for future in as_completed(futures):
            result = future.result()
            if result[0] == 'ok':
                uploaded += 1
            else:
                errors += 1
                log(f"  Upload error: {result[1]} — {result[2]}")
            if (uploaded + errors) % 100 == 0:
                log(f"  Progress: {uploaded+errors}/{total} ({uploaded} ok, {errors} err)")

    log(f"Upload done: {uploaded} uploaded, {errors} errors")
    shutil.rmtree(str(work))
    log(f"Local cleaned: {name}")
    log(f"=== Done: {name} ===\n")

    return {'name': name, 'url': folder_url, 'categories': categories, 'uploaded': uploaded, 'errors': errors}


if __name__ == '__main__':
    os.makedirs(WORK_DIR, exist_ok=True)
    log("=== Pipeline v2 (8 parallel threads) ===")

    results = []
    for z in ZIPS:
        try:
            r = process_zip(z)
            if r:
                results.append(r)
                log(f"SUMMARY {r['name']}: {r['uploaded']} files | {r['categories']} | {r['url']}")
        except Exception as e:
            import traceback
            log(f"FATAL on {z['name']}: {e}\n{traceback.format_exc()}")

    log("=== ALL DONE ===")
    for r in results:
        log(f"  {r['name']}: {r['uploaded']} files — {r['url']}")
