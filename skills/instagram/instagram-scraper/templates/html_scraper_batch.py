#!/usr/bin/env python3
"""
HTML Scraper Fallback for Instagram Profiles
Use when API is rate-limited (429) but HTML parsing still works.
Safe for batch crawling: 1–2 sec/profile, low bot-detection risk.
"""

import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
from datetime import datetime

def load_cookies(cookie_file=None):
    """Load Instagram session cookies from vault."""
    if not cookie_file:
        cookie_file = Path.home() / ".hermes" / ".ig_cookies.json"
    
    with open(cookie_file) as f:
        cookies_data = json.load(f)
    
    return {k: cookies_data[k] for k in ["datr", "ds_user_id", "csrftoken", "ig_did", "mid", "sessionid"]}

def scrape_profile(username, cookies, headers=None, timeout=8):
    """
    Scrape a single Instagram profile using HTML parsing.
    Returns: dict with username, status, bio, timestamp
    """
    if not headers:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        url = f"https://www.instagram.com/{username}/"
        response = requests.get(url, cookies=cookies, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract bio from og:description meta tag
            og_desc = soup.find("meta", property="og:description")
            bio = og_desc.get("content", "")[:100] if og_desc else ""
            
            return {
                "username": username,
                "status": "success",
                "bio": bio,
                "crawled_at": datetime.now().isoformat()
            }
        else:
            return {"username": username, "status": f"error_{response.status_code}"}
    
    except Exception as e:
        return {"username": username, "status": "error", "error": type(e).__name__}

def crawl_batch(usernames, cookies, output_file=None, stagger_delay=1.2):
    """
    Crawl multiple profiles with staggered requests to avoid detection.
    
    Args:
        usernames: List of Instagram usernames
        cookies: Session cookies dict (from load_cookies)
        output_file: Path to save JSON results (default: /tmp/ig_html_crawl.json)
        stagger_delay: Delay between requests in seconds (default: 1.2)
    
    Returns: List of results dicts
    """
    if not output_file:
        output_file = "/tmp/ig_html_crawl.json"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    results = []
    success_count = 0
    
    print(f"\nCrawling {len(usernames)} profiles via HTML scraper...\n")
    
    for i, username in enumerate(usernames, 1):
        result = scrape_profile(username, cookies, headers)
        results.append(result)
        
        if result["status"] == "success":
            success_count += 1
            print(f"  {i:2d}. ✅ {username}")
        else:
            print(f"  {i:2d}. ❌ {username}")
        
        # Stagger requests to avoid bot detection
        if i < len(usernames):
            time.sleep(stagger_delay)
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "method": "HTML parsing",
            "total": len(usernames),
            "success": success_count,
            "failed": len(usernames) - success_count,
            "results": results
        }, f, indent=2)
    
    print(f"\n✅ Crawl complete: {success_count}/{len(usernames)} profiles")
    print(f"   Results saved: {output_file}")
    
    return results

# Example usage:
if __name__ == "__main__":
    cookies = load_cookies()
    
    test_usernames = [
        "instagram", "cristiano", "leoniemhikes", "katharinarose", "emrata"
    ]
    
    results = crawl_batch(test_usernames, cookies)
