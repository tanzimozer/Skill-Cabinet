#!/usr/bin/env python3
"""
Fitness Trainer Skill — Sheet Utilities
Handles: sheet creation, tab setup, assessment population, approval stamping.
Auth: ~/.hermes/google_token.json
"""

import json
import sys
import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = os.path.expanduser("~/.hermes/google_token.json")
TANZIM_EMAIL = "tanzim.seattle@gmail.com"


def get_services():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return sheets, drive


def create_fitness_sheet(client_name: str) -> dict:
    """
    Create a new Google Sheet named '[Name] Fitness Profile'.
    Sets up Assessment, Training, Nutrition tabs.
    Shares with Tanzim.
    Returns: { "sheet_id": str, "url": str }
    """
    sheets_svc, drive_svc = get_services()

    # Create spreadsheet with three tabs
    body = {
        "properties": {"title": f"{client_name} Fitness Profile"},
        "sheets": [
            {"properties": {"title": "Assessment", "index": 0}},
            {"properties": {"title": "Training", "index": 1}},
            {"properties": {"title": "Nutrition", "index": 2}},
        ],
    }
    spreadsheet = sheets_svc.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    sheet_id = spreadsheet["spreadsheetId"]
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"

    # Share with Tanzim
    drive_svc.permissions().create(
        fileId=sheet_id,
        body={"type": "user", "role": "writer", "emailAddress": TANZIM_EMAIL},
        sendNotificationEmail=False,
    ).execute()

    # Set up Assessment tab headers
    _setup_assessment_tab(sheets_svc, sheet_id)

    print(json.dumps({"sheet_id": sheet_id, "url": url}))
    return {"sheet_id": sheet_id, "url": url}


def _setup_assessment_tab(sheets_svc, sheet_id: str):
    """Write assessment field headers and format the tab."""
    fields = [
        "Full Name",
        "Age",
        "Primary Goal",
        "Current Weight",
        "Height",
        "Body Fat %",
        "Training Experience Level",
        "Years Training",
        "Training Days Per Week",
        "Training Location",
        "Equipment Access",
        "Injuries / Limitations",
        "Dietary Restrictions / Allergies",
        "Current Eating Habits / Diet",
        "Current Supplements",
    ]

    header_values = [["Field", "Client Response"]]
    field_values = [[f] for f in fields]
    all_values = header_values + field_values

    sheets_svc.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Assessment!A1",
        valueInputOption="RAW",
        body={"values": all_values},
    ).execute()

    tab_id = _get_sheet_tab_id(sheets_svc, sheet_id, "Assessment")

    requests = [
        # Bold header row
        {
            "repeatCell": {
                "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        },
        # Bold column A
        {
            "repeatCell": {
                "range": {"sheetId": tab_id, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        },
        # Freeze row 1
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": tab_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
        # Column A width = 250px
        {
            "updateDimensionProperties": {
                "range": {"sheetId": tab_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 250},
                "fields": "pixelSize",
            }
        },
        # Column B width = 400px
        {
            "updateDimensionProperties": {
                "range": {"sheetId": tab_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                "properties": {"pixelSize": 400},
                "fields": "pixelSize",
            }
        },
    ]
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": requests}
    ).execute()


def _get_sheet_tab_id(sheets_svc, sheet_id: str, tab_name: str) -> int:
    """Return the sheetId integer for a named tab."""
    meta = sheets_svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
    for sheet in meta["sheets"]:
        if sheet["properties"]["title"] == tab_name:
            return sheet["properties"]["sheetId"]
    raise ValueError(f"Tab '{tab_name}' not found in sheet {sheet_id}")


def populate_assessment(sheet_id: str, responses: dict):
    """
    Write client responses into Assessment tab column B.
    responses: dict mapping field name to client's answer.
    """
    sheets_svc, _ = get_services()

    fields = [
        "Full Name",
        "Age",
        "Primary Goal",
        "Current Weight",
        "Height",
        "Body Fat %",
        "Training Experience Level",
        "Years Training",
        "Training Days Per Week",
        "Training Location",
        "Equipment Access",
        "Injuries / Limitations",
        "Dietary Restrictions / Allergies",
        "Current Eating Habits / Diet",
        "Current Supplements",
    ]

    values = [[responses.get(f, "")] for f in fields]

    sheets_svc.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Assessment!B2",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()
    print(f"Assessment tab populated for sheet {sheet_id}")


def stamp_approval(sheet_id: str):
    """
    Append approval stamp to bottom of Assessment, Training, and Nutrition tabs.
    Format: bold, dark green (#1a7a1a).
    """
    sheets_svc, _ = get_services()
    date_str = datetime.now().strftime("%d %b %Y")
    stamp_text = f"Approved by Tanzim Ozer CPT, SNS — {date_str}"

    tabs = ["Assessment", "Training", "Nutrition"]

    for tab in tabs:
        tab_id = _get_sheet_tab_id(sheets_svc, sheet_id, tab)

        result = sheets_svc.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{tab}!A:A"
        ).execute()
        existing = result.get("values", [])
        last_row = len(existing)
        stamp_row = last_row + 3  # 2 blank rows gap

        sheets_svc.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{tab}!A{stamp_row}",
            valueInputOption="RAW",
            body={"values": [[stamp_text]]},
        ).execute()

        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": stamp_row - 1,
                        "endRowIndex": stamp_row,
                        "startColumnIndex": 0,
                        "endColumnIndex": 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {
                                    "red": 0.102,
                                    "green": 0.478,
                                    "blue": 0.102,
                                },
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat",
                }
            }
        ]
        sheets_svc.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body={"requests": requests}
        ).execute()
        print(f"Stamped: {tab}")

    print("All tabs stamped.")


def write_tab_content(sheet_id: str, tab_name: str, content_rows: list):
    """
    Write generated content (training/nutrition) into a tab.
    Clears existing content first, then writes from A1.
    content_rows: list of lists.
    """
    sheets_svc, _ = get_services()

    sheets_svc.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1:Z1000",
    ).execute()

    sheets_svc.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        valueInputOption="RAW",
        body={"values": content_rows},
    ).execute()
    print(f"{tab_name} tab written ({len(content_rows)} rows)")


if __name__ == "__main__":
    """
    CLI usage:
      python3 fitness_trainer.py create "Blair"
      python3 fitness_trainer.py stamp "SHEET_ID"
    """
    if len(sys.argv) < 2:
        print("Usage: fitness_trainer.py [create|stamp] [args]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "create" and len(sys.argv) == 3:
        create_fitness_sheet(sys.argv[2])
    elif cmd == "stamp" and len(sys.argv) == 3:
        stamp_approval(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
