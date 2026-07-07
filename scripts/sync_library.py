#!/usr/bin/env python3
"""Merge newly-saved Sublime items into library-sync-state.json and re-render
library.html. Used by the daily Sublime -> jackraines.blog sync job.

Usage:
    python3 scripts/sync_library.py --state library-sync-state.json \\
        --html library.html --candidates /tmp/candidates.json

candidates.json is a JSON list of objects, one per card returned by the
Sublime MCP tool's get_collection_items, each with:
    {"section": "Everything I'm Reading", "title": "...", "source_url": "...",
     "entity_type": "article"|"tweet"|"link"|"file"|"highlight"|...,
     "date_added": "YYYY-MM-DD" (optional; defaults to today)}

Only genuinely new items (by normalized URL) are added. File-type cards and
title-less/source-less highlights are skipped. Prints how many items were
added, and by which section, as JSON on stdout.
"""
import argparse
import json
import re
import sys
from datetime import date, datetime
from urllib.parse import urlsplit, parse_qsl, urlencode

SECTION_ORDER = [
    "Everything I'm Reading",
    "Useful Learnings",
    "Newsletter Topics",
    "Work-Related Links",
    "X Bookmarks",
]

TRACKING_PARAMS = re.compile(
    r"^(utm_.*|mkt_tok|si|fbclid|gclid|ref|reflink|trackingid|smid|st|triedredirect|hide_intro_popup)$",
    re.IGNORECASE,
)


def tweet_handle(url):
    m = re.search(r"x\.com/([^/]+)/status/", url, re.IGNORECASE)
    return m.group(1) if m else None


def ensure_scheme(url):
    if not re.match(r"^https?://", url, re.IGNORECASE):
        return "https://" + url
    return url


def normalize_key(url):
    parts = urlsplit(url.lower())
    netloc = parts.netloc[4:] if parts.netloc.startswith("www.") else parts.netloc
    q = [(k, v) for k, v in parse_qsl(parts.query) if not TRACKING_PARAMS.match(k)]
    query = urlencode(sorted(q))
    path = parts.path.rstrip("/")
    return f"{netloc}{path}?{query}" if query else f"{netloc}{path}"


def domain_of(url):
    netloc = urlsplit(url).netloc
    return netloc[4:] if netloc.startswith("www.") else netloc


def build_item(candidate, today):
    url = ensure_scheme(candidate["source_url"].strip())
    entity_type = candidate.get("entity_type", "").lower()
    if entity_type == "tweet":
        handle = tweet_handle(url)
        title = f"Tweet by @{handle}" if handle else "Tweet"
    else:
        title = " ".join((candidate.get("title") or "").split())
        if not title:
            title = domain_of(url)
    date_added = candidate.get("date_added") or today
    return {
        "key": normalize_key(url),
        "url": url,
        "title": title,
        "source": domain_of(url),
        "section": candidate["section"],
        "date_added": date_added,
    }


def load_state(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"items": []}


def merge(state, candidates, today):
    existing_keys = {it["key"] for it in state["items"]}
    added = []
    for c in candidates:
        if c.get("entity_type", "").lower() == "file":
            continue
        if c.get("entity_type", "").lower() == "highlight" and not (c.get("title") or "").strip() and not (c.get("source_url") or "").strip():
            continue
        if not (c.get("source_url") or "").strip():
            continue
        item = build_item(c, today)
        if item["key"] in existing_keys:
            continue
        existing_keys.add(item["key"])
        state["items"].append(item)
        added.append(item)
    return added


def reconcile_titles(state, html_path):
    """Pull any manually-edited titles from the currently-published HTML back
    into the state file, so a from-scratch regeneration doesn't clobber
    hand-cleaned titles (e.g. fixing a placeholder like "Just a moment...").
    Matched by normalized URL key, same as dedup."""
    import html as htmlmod
    try:
        with open(html_path) as f:
            current = f.read()
    except FileNotFoundError:
        return 0
    pattern = re.compile(r'<li><a href="([^"]+)">(.*?)</a>')
    live_titles = {}
    for m in pattern.finditer(current):
        url = htmlmod.unescape(m.group(1))
        title = htmlmod.unescape(m.group(2))
        live_titles[normalize_key(url)] = title
    updated = 0
    for it in state["items"]:
        live = live_titles.get(it["key"])
        if live and live != it["title"]:
            it["title"] = live
            updated += 1
    return updated


def split_header_footer(html_path):
    """Preserve whatever header (nav/h1/intro) and footer currently exist in
    the published page verbatim, so nav redesigns or copy edits made outside
    this script aren't reverted by a sync. Splits on the first <ul (the start
    of the rendered list, regardless of whether section <h2>s are present)
    and the last </ul>."""
    with open(html_path) as f:
        current = f.read()
    # Match <h2 too (not just <ul) so this cleanly cuts off a leftover
    # section heading from before section headers were removed.
    content_match = re.search(r"^ {4}<(ul|h2)\b", current, re.MULTILINE)
    if not content_match:
        raise ValueError(f"No <ul> or <h2> found in {html_path}")
    first_ul = content_match.start()
    last_ul_close = current.rindex("</ul>") + len("</ul>")
    header = current[:first_ul].rstrip("\n")
    footer = current[last_ul_close:].lstrip("\n")
    return header, footer


def render_html(state, html_path):
    header, footer = split_header_footer(html_path)

    def sort_key(it):
        try:
            return datetime.strptime(it["date_added"], "%Y-%m-%d")
        except (TypeError, ValueError):
            return datetime.min

    items = sorted(state["items"], key=sort_key, reverse=True)

    def render_item(it):
        import html as htmlmod
        label = htmlmod.escape(it["title"])
        url = htmlmod.escape(it["url"], quote=True)
        source_html = f' <span class="source">{htmlmod.escape(it["source"])}</span>' if it["source"] else ""
        date_html = ""
        try:
            d = datetime.strptime(it["date_added"], "%Y-%m-%d")
            date_str = d.strftime("%B ") + str(d.day) + d.strftime(", %Y")
            date_html = f' <span class="date">({date_str})</span>'
        except (TypeError, ValueError):
            pass
        return f'        <li><a href="{url}">{label}</a>{source_html}{date_html}</li>'

    lis = "\n".join(render_item(it) for it in items)
    body = f'    <ul class="essay-list">\n{lis}\n    </ul>'

    page = f"{header}\n\n{body}\n\n{footer}"
    with open(html_path, "w") as f:
        f.write(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--html", required=True)
    ap.add_argument("--candidates", required=True)
    args = ap.parse_args()

    state = load_state(args.state)
    reconcile_titles(state, args.html)

    with open(args.candidates) as f:
        candidates = json.load(f)

    today = date.today().isoformat()
    added = merge(state, candidates, today)

    with open(args.state, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")

    render_html(state, args.html)

    by_section = {}
    for it in added:
        by_section[it["section"]] = by_section.get(it["section"], 0) + 1
    print(json.dumps({"added": len(added), "by_section": by_section}))


if __name__ == "__main__":
    sys.exit(main())
