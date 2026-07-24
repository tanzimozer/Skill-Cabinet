#!/usr/bin/env python3
"""
enrich.py — Layer 1/2/3 pass over raw handles → the provider database.

Takes out/handles.csv (raw catch), visits each profile with the same live
cookies, extracts the wide schema (see SCHEMA.md), scores fitness, flags city,
applies the band filter, and writes to the Google Sheet (Providers / Rejected /
Raw tabs). Nothing is deleted — out-of-band rows are tagged and parked.

This is a scaffold: the profile-field extraction and Sheets write are marked
TODO for the Mac-side run (needs live cookies + google_token.json). The scoring,
city, and band logic are complete and testable offline.

Usage:
    python enrich.py [--in out/handles.csv] [--city seattle] [--min 150] [--max 3500]
"""
import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CITIES = json.loads((ROOT / "cities.json").read_text())

FITNESS_KW = ["coach", "gym", "fit", "fitness", "pt ", "personal trainer", "macros",
              "transformation", "kg", "reps", "athlete", "nutrition", "wellness",
              "training", "workout", "lift", "wod", "crossfit", "dm for plans"]


def fitness_score(bio, name, category, has_link, eng_proxy):
    text = f"{bio or ''} {name or ''}".lower()
    hits = sum(1 for k in FITNESS_KW if k in text)
    score = min(hits * 12, 60)
    if has_link:
        score += 15
    if category and any(w in category.lower() for w in ("fit", "athlete", "trainer", "sport", "coach")):
        score += 15
    if eng_proxy and eng_proxy > 0.03:
        score += 10
    return min(score, 100)


def city_flag(bio, tagged_locations, city="seattle"):
    dic = CITIES.get(city, {})
    text = f"{bio or ''} {' '.join(tagged_locations or [])}".lower()
    if any(w in text for w in dic.get("strong", [])):
        return "yes", city
    if any(w in text for w in dic.get("weak", [])):
        return "maybe", city
    return "", ""


def band(followers, lo, hi):
    if followers is None:
        return "unknown"
    if lo <= followers <= hi:
        return "yes"
    edge_lo, edge_hi = lo * 0.9, hi * 1.1
    if edge_lo <= followers <= edge_hi:
        return "maybe"
    return "no"


def enrich_profile(handle):
    """TODO (Mac-side): visit instagram.com/<handle> with live cookies, parse
    followers/following/posts/bio/link/category/verified/private/last_post/eng.
    Returns a dict matching SCHEMA.md. Stubbed here for offline logic testing."""
    return {
        "handle": handle, "full_name": "", "followers": None, "following": None,
        "posts": None, "bio": "", "external_link": "", "ig_category": "",
        "account_type": "", "verified": False, "is_private": False,
        "last_post_date": "", "eng_proxy": None, "tagged_locations": [],
    }


def process(in_path, city, lo, hi):
    rows_in = list(csv.DictReader(open(in_path)))
    providers, rejected = [], []
    for r in rows_in:
        p = enrich_profile(r["handle"])
        has_link = bool(p["external_link"])
        p["follow_ratio"] = (p["following"] / p["followers"]) if p["followers"] else None
        p["link_domain"] = re.sub(r"^https?://(www\.)?", "", p["external_link"]).split("/")[0] if has_link else ""
        p["fitness_score"] = fitness_score(p["bio"], p["full_name"], p["ig_category"], has_link, p["eng_proxy"])
        seattle, match = city_flag(p["bio"], p["tagged_locations"], city)
        p["seattle"], p["city_match"] = seattle, match
        p["in_band"] = band(p["followers"], lo, hi)
        p["source"] = r.get("source", "")
        (rejected if p["in_band"] == "no" else providers).append(p)
    print(f"providers: {len(providers)} | rejected(out-of-band): {len(rejected)}")
    # TODO (Mac-side): write providers/rejected/raw to the Google Sheet with
    # header bold+centred+frozen, cells left+wrap+top, numeric formats, score colour.
    return providers, rejected


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", default=str(ROOT / "out" / "handles.csv"))
    ap.add_argument("--city", default="seattle")
    ap.add_argument("--min", type=int, default=150)
    ap.add_argument("--max", type=int, default=3500)
    a = ap.parse_args()
    process(a.in_path, a.city, a.min, a.max)
