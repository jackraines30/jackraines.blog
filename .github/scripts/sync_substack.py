#!/usr/bin/env python3
"""
Syncs new Young Money Substack posts into writing.html.
Reads the RSS feed, finds posts newer than the most recent one
already listed, and prepends them to the Essays section.
"""

import re
import feedparser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEED_URL = "https://www.youngmoney.co/feed"
WRITING_HTML = "writing.html"

# Posts to skip (promotional, not essays)
SKIP_KEYWORDS = [
    "preorder your copy",
    "check out young money, the book",
]

def should_skip(title: str) -> bool:
    return any(kw in title.lower() for kw in SKIP_KEYWORDS)

def parse_existing_dates(html: str) -> list[datetime]:
    """Extract all dates already listed in the Essays section."""
    # Match dates in the format (Month Day, Year)
    pattern = r'\((\w+ \d+, \d{4})\)'
    matches = re.findall(pattern, html)
    dates = []
    for m in matches:
        try:
            dates.append(datetime.strptime(m, "%B %d, %Y").replace(tzinfo=timezone.utc))
        except ValueError:
            pass
    return dates

def format_entry(title: str, url: str, date: datetime) -> str:
    date_str = date.strftime("%B %-d, %Y")
    # Escape quotes in title
    escaped_title = title.replace('"', '&quot;').replace("'", "&#x27;")
    return (
        f'        <li>'
        f'<a href="{url}">{escaped_title}</a> '
        f'<span class="date">({date_str})</span>'
        f'</li>'
    )

def main():
    # Read current writing.html
    with open(WRITING_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    # Find the most recent date already in the file
    existing_dates = parse_existing_dates(html)
    if not existing_dates:
        print("Could not find any existing dates in writing.html. Aborting.")
        return
    most_recent = max(existing_dates)
    print(f"Most recent post already listed: {most_recent.strftime('%B %-d, %Y')}")

    # Fetch the RSS feed
    feed = feedparser.parse(FEED_URL)
    if not feed.entries:
        print("No entries found in RSS feed.")
        return

    # Collect new posts (newer than most_recent, not skipped)
    new_entries = []
    for entry in feed.entries:
        try:
            pub_date = parsedate_to_datetime(entry.published).replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if pub_date.date() <= most_recent.date():
            continue

        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()

        if should_skip(title):
            print(f"Skipping promotional post: {title}")
            continue

        new_entries.append((pub_date, title, url))

    if not new_entries:
        print("No new posts to add.")
        return

    # Sort newest first
    new_entries.sort(key=lambda x: x[0], reverse=True)

    # Build the HTML lines to insert
    new_lines = "\n".join(format_entry(title, url, date) for date, title, url in new_entries)
    print(f"Adding {len(new_entries)} new post(s):")
    for date, title, url in new_entries:
        print(f"  - {title} ({date.strftime('%B %-d, %Y')})")

    # Insert after the opening <ul> tag in the Essays section
    # Find the <ul> that immediately follows the Essays <h2>
    essays_marker = re.search(r'(<h2[^>]*>Essays</h2>\s*<ul[^>]*>)', html, re.IGNORECASE)
    if not essays_marker:
        # Fallback: find any <ul> in the essays region
        ul_match = re.search(r'(<ul[^>]*>)', html)
        if not ul_match:
            print("Could not find <ul> in writing.html. Aborting.")
            return
        insert_pos = ul_match.end()
    else:
        insert_pos = essays_marker.end()

    updated_html = html[:insert_pos] + "\n" + new_lines + "\n" + html[insert_pos:]

    with open(WRITING_HTML, "w", encoding="utf-8") as f:
        f.write(updated_html)

    print("writing.html updated successfully.")

if __name__ == "__main__":
    main()
