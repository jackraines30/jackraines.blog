#!/usr/bin/env python3
"""Sync library-sync-state.json / library.html from raw Sublime collection
dumps, instead of a hand-built candidates.json. The nightly agent's only job
is to call get_collection_items for each collection and save the tool's
output verbatim (via --dump section=filepath, repeatable) -- all parsing and
merging is deterministic from here on, removing the hand-transcription step
that caused a silent miss on 2026-07-08.

Usage:
    python3 scripts/sync_from_dumps.py \\
        --state library-sync-state.json --html library.html --log library-sync-log.jsonl \\
        --dump "Everything I'm Reading=/tmp/dump_diet.txt" \\
        --dump "Useful Learnings=/tmp/dump_useful.txt" \\
        --dump "Newsletter Topics=/tmp/dump_newsletter.txt" \\
        --dump "Work-Related Links=/tmp/dump_work.txt" \\
        --dump "X Bookmarks=/tmp/dump_xbookmarks.txt"
"""
import argparse
import json
import sys
from datetime import date, datetime

from parse_sublime_dump import parse_dump
from sync_library import load_state, merge, render_html, reconcile_titles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--html", required=True)
    ap.add_argument("--log", default="library-sync-log.jsonl")
    ap.add_argument("--dump", action="append", required=True,
                     help="section=filepath, repeatable")
    ap.add_argument("--note", default=None,
                     help="Optional note to record in the log (e.g. a tool failure).")
    args = ap.parse_args()

    state = load_state(args.state)
    reconcile_titles(state, args.html)

    candidates = []
    dump_counts = {}
    for spec in args.dump:
        section, path = spec.split("=", 1)
        with open(path) as f:
            text = f.read()
        items = parse_dump(text, section)
        dump_counts[section] = len(items)
        candidates.extend(items)

    today = date.today().isoformat()
    added = merge(state, candidates, today)

    with open(args.state, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")

    render_html(state, args.html)

    by_section = {}
    for it in added:
        by_section[it["section"]] = by_section.get(it["section"], 0) + 1

    log_entry = {
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "candidates_seen": len(candidates),
        "candidates_by_section": dump_counts,
        "added": len(added),
        "by_section": by_section,
    }
    if args.note:
        log_entry["note"] = args.note
    with open(args.log, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(json.dumps({"added": len(added), "by_section": by_section, "candidates_by_section": dump_counts}))


if __name__ == "__main__":
    sys.exit(main())
