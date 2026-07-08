"""Deterministically parse the Sublime MCP tool's get_collection_items text
output into candidate dicts, so a nightly agent never has to hand-transcribe
items into JSON (the actual cause of a silent miss on 2026-07-08: an LLM
retyping ~50 items by hand from freeform text is exactly the kind of
repetitive task that drops entries at scale)."""
import re

ITEM_RE = re.compile(
    r"^\d+\.\s+\*\*(.*?)\*\*\s*\((\w+)\)\s*\n(.*?)(?=^\d+\.\s+\*\*|\Z)",
    re.MULTILINE | re.DOTALL,
)
SOURCE_RE = re.compile(r"^\s*Source:\s*(\S+)", re.MULTILINE)


def parse_dump(text, section):
    """Returns a list of candidate dicts: section, title, source_url, entity_type.
    Items with no 'Source:' line (e.g. untitled highlights) are skipped, same
    as the existing exclusion policy."""
    candidates = []
    for m in ITEM_RE.finditer(text):
        title = " ".join(m.group(1).split())
        entity_type = m.group(2).lower()
        body = m.group(3)
        src_match = SOURCE_RE.search(body)
        if not src_match:
            continue
        candidates.append({
            "section": section,
            "title": title,
            "source_url": src_match.group(1),
            "entity_type": entity_type,
        })
    return candidates
