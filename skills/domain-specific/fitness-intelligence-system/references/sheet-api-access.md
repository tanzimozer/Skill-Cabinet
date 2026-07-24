# Sheet API Access: Loading TIMBR Fitness Data

## Sheet Metadata

**Spreadsheet ID:** `1Tb3OHcuIkCIbIL59k60BhBEiCMw5fnjOenUO1isBefo`

**Tabs:**
1. Pairings (gid=0) — Muscle pairing rules
2. Stage 1 — Foundation 0 (gid=2001)
3. Stage 2 — Foundation 1 (gid=2002)
4. Stage 3 — Strength 1 / Performance 1 (gid=2003)
5. Stage 4 — Foundation 2 (gid=2004)
6. Stage 5 — Strength 2 / Performance 2 (gid=2005)
7. Stage 6 — Performance 2 (MB) / Strength 2 (FL) (gid=2006)
8. Stage 7 — Foundation 3 (gid=2007)
9. Stage 8 — Strength 3 / Performance 3 (gid=2008)
10. Stage 9 — Performance 3 (MB) / Strength 3 (FL) (gid=2009)

## Loading Pairings Tab

The Pairings tab has two sections: "WHAT'S RIGHT" (approved) and "WHAT'S WRONG" (forbidden).

```python
import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load Google OAuth
token_path = os.path.expanduser('~/.hermes/google_token.json')
with open(token_path) as f:
    token_data = json.load(f)

creds = Credentials.from_authorized_user_info(
    token_data,
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
)

sheets = build('sheets', 'v4', credentials=creds)
spreadsheet_id = '1Tb3OHcuIkCIbIL59k60BhBEiCMw5fnjOenUO1isBefo'

# Fetch the Pairings tab (entire sheet)
result = sheets.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range="'Pairings'!A:D"
).execute()

values = result.get('values', [])

# Parse approved and forbidden
approved_pairings = []
forbidden_pairings = []
current_section = None

for row in values:
    if not row:
        continue
    
    if 'WHAT' in str(row[0]):
        if 'RIGHT' in str(row[0]):
            current_section = 'approved'
        elif 'WRONG' in str(row[0]):
            current_section = 'forbidden'
        continue
    
    if current_section and len(row) >= 3 and row[0] and row[0] not in ['Muscle A', '']:
        pair = {
            'muscle_a': row[0].strip(),
            'muscle_b': row[1].strip() if len(row) > 1 else '',
            'reason': row[2].strip() if len(row) > 2 else ''
        }
        
        if current_section == 'approved':
            approved_pairings.append(pair)
        else:
            forbidden_pairings.append(pair)

print(f"✓ Loaded {len(approved_pairings)} approved pairings")
print(f"✓ Loaded {len(forbidden_pairings)} forbidden pairings")
```

## Loading Stage Data

Each stage tab has a similar structure: a grid indexed by [frequency][gender][day].

**Example: Stage 1 — Foundation 0**

The tab is organized as:

```
Row 1: Headers
Row 2-8: 3 days/week — Male (Days 1-7)
Row 10-16: 3 days/week — Female (Days 1-7)
Row 18-24: 4 days/week — Male (Days 1-7)
...and so on
```

Each cell contains the muscle groups for that day (e.g., "Chest + Triceps", "Rest", "Back + Biceps").

```python
def load_stage(sheets, spreadsheet_id, stage_name):
    """Load all workout data from a stage tab."""
    
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{stage_name}'!A:G"
    ).execute()
    
    values = result.get('values', [])
    
    stage_data = {}
    
    for freq in ['3 days/week', '4 days/week', '5 days/week']:
        stage_data[freq] = {}
        
        for gender in ['Male', 'Female']:
            # Find the block for this freq+gender combo
            key = f"{freq} — {gender}"
            stage_data[freq][gender] = {
                'Day 1': None,
                'Day 2': None,
                # ... Day 3-7
            }
    
    # Simple parser (exact row structure varies per stage)
    # In practice, scan for header rows and build lookup table
    return stage_data

# Load all 9 stages
stages = {}
for i in range(1, 10):
    stage_name = f"Stage {i}"  # Adjust to actual names
    stages[stage_name] = load_stage(sheets, spreadsheet_id, stage_name)
    print(f"✓ Loaded {stage_name}")
```

## Lookup Pattern

```python
class FitnessDataStore:
    def __init__(self, approved_pairs, forbidden_pairs, stage_data):
        self.approved_pairs = approved_pairs
        self.forbidden_pairs = forbidden_pairs
        self.stage_data = stage_data
    
    def get_daily_split(self, stage, frequency, gender, day):
        """Return muscle groups for a specific day."""
        try:
            return self.stage_data[stage][frequency][gender][f'Day {day}']
        except KeyError:
            return None
    
    def validate_pairing(self, muscle_a, muscle_b):
        """Check if pairing is approved."""
        pair = tuple(sorted([muscle_a, muscle_b]))
        
        for forbidden in self.forbidden_pairs:
            f_pair = tuple(sorted([forbidden['muscle_a'], forbidden['muscle_b']]))
            if pair == f_pair:
                return {'valid': False, 'reason': forbidden['reason']}
        
        for approved in self.approved_pairs:
            a_pair = tuple(sorted([approved['muscle_a'], approved['muscle_b']]))
            if pair == a_pair:
                return {'valid': True, 'reason': approved['reason']}
        
        return {'valid': False, 'reason': 'pairing not validated'}
```

## Full Load Routine (Production)

```python
import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def load_fitness_data(spreadsheet_id='1Tb3OHcuIkCIbIL59k60BhBEiCMw5fnjOenUO1isBefo'):
    """Load all TIMBR fitness data from Google Sheets."""
    
    # Setup
    token_path = os.path.expanduser('~/.hermes/google_token.json')
    with open(token_path) as f:
        token_data = json.load(f)
    
    creds = Credentials.from_authorized_user_info(
        token_data,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    
    sheets = build('sheets', 'v4', credentials=creds)
    
    # 1. Load Pairings
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="'Pairings'!A:D"
    ).execute()
    
    # Parse (see above)
    approved = [...]
    forbidden = [...]
    
    # 2. Load Stages
    stages = {}
    stage_names = [
        'Stage 1 — Foundation 0',
        'Stage 2 — Foundation 1',
        'Stage 3 — Strength 1 / Performance 1',
        'Stage 4 — Foundation 2',
        'Stage 5 — Strength 2 / Performance 2',
        'Stage 6 — Performance 2 (MB) / Strength 2 (FL)',
        'Stage 7 — Foundation 3',
        'Stage 8 — Strength 3 / Performance 3',
        'Stage 9 — Performance 3 (MB) / Strength 3 (FL)',
    ]
    
    for stage_name in stage_names:
        # Load stage
        stages[stage_name] = load_stage(sheets, spreadsheet_id, stage_name)
    
    return {
        'approved_pairings': approved,
        'forbidden_pairings': forbidden,
        'stages': stages
    }

# Usage
fitness_data = load_fitness_data()
print(f"✓ Loaded {len(fitness_data['approved_pairings'])} approved pairings")
print(f"✓ Loaded {len(fitness_data['stages'])} stages")
```

## Error Handling

**Token expired:** Refresh using the pattern in `google-oauth-refresh` skill.

**Tab not found:** Double-check sheet names in the metadata above. Tab names are exact (including dashes, slashes, spaces).

**No read access:** Ensure `scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']` is set. If token doesn't have this scope, full re-auth is needed.

**Rate limit (429):** Add `time.sleep(0.2)` between batch requests. Google Sheets API allows ~1000 reads per 100 seconds.
