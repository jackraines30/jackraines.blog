#!/usr/bin/env python3
"""Fetch raw dump text for the 5 library collections directly from Sublime's
MCP endpoint over plain HTTP/JSON-RPC -- no Claude session involved. Writes
one dump file per collection, in the same verbatim text format the sync
script already expects (see scripts/parse_sublime_dump.py).

Requires env var SUBLIME_MCP_TOKEN.
"""
import json
import os
import sys
import urllib.request

COLLECTIONS = [
    ("187db325-7215-48d0-b9a5-ffbb69656927", "Everything I'm Reading", "dump_diet.txt"),
    ("de3f9b0a-32f5-4a8a-bdb8-35e6bc023cde", "Useful Learnings", "dump_useful.txt"),
    ("9537ef9c-69a5-4998-9070-f507102af1be", "Newsletter Topics", "dump_newsletter.txt"),
    ("d675e59b-b6fc-4fba-aefb-30ff4a03d206", "Work-Related Links", "dump_work.txt"),
    ("e049625d-4a3a-4c1e-a4e3-69fd04f11887", "X Bookmarks", "dump_xbookmarks.txt"),
]


def post(url, payload, session_id=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        session_id = resp.headers.get("Mcp-Session-Id", session_id)
        body = resp.read().decode()
    return body, session_id


def parse_sse_json(body):
    for line in body.splitlines():
        if line.startswith("data:"):
            return json.loads(line[len("data:"):].strip())
    return json.loads(body)


def main():
    token = os.environ["SUBLIME_MCP_TOKEN"]
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    url = f"https://mcp.sublime.app/mcp?token={token}"

    _, session_id = post(url, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "gha-sync", "version": "0.1"}},
    })
    post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id)

    counts = {}
    for idx, (collection_id, section, filename) in enumerate(COLLECTIONS, start=2):
        body, session_id = post(url, {
            "jsonrpc": "2.0", "id": idx, "method": "tools/call",
            "params": {"name": "get_collection_items",
                       "arguments": {"collection_id": collection_id, "limit": 50,
                                     "order_by": "-first_connection_at"}},
        }, session_id)
        msg = parse_sse_json(body)
        if "error" in msg:
            print(f"ERROR fetching {section}: {msg['error']}", file=sys.stderr)
            sys.exit(1)
        text = msg["result"]["content"][0]["text"]
        path = os.path.join(out_dir, filename)
        with open(path, "w") as f:
            f.write(text)
        counts[section] = text

    print(json.dumps({"fetched": list(counts.keys())}))


if __name__ == "__main__":
    main()
