# jackraines.blog

My personal website. Haters stay away.

## Automation

### Weekly Substack Sync

A GitHub Action runs every Monday at 9am EDT to automatically keep the [Writing page](https://jackraines.blog/writing) up to date with new posts from the [Young Money Substack](https://www.youngmoney.co).

**How it works:**
1. Fetches the Young Money RSS feed (`https://www.youngmoney.co/feed`)
2. Compares against posts already listed in `writing.html`
3. Prepends any new essays to the top of the list (newest first)
4. Commits and pushes the update automatically

**Files:**
- `.github/workflows/sync_substack.yml` — the workflow schedule and steps
- `.github/scripts/sync_substack.py` — the Python script that does the syncing

**Manual trigger:**
You can also run the sync on demand from the [Actions tab](../../actions/workflows/sync_substack.yml) by clicking "Run workflow."

**Skipped posts:**
Promotional posts (book announcements, etc.) are filtered out automatically and won't appear on the writing page.

### Daily Sublime Library Sync

A scheduled agent session runs every night at 9pm ET to keep the [Library page](https://jackraines.blog/library) up to date with new saves from [Sublime](https://sublime.app).

**How it works:**
1. Fetches the 5 tracked Sublime collections (Jack's content diet, Useful Learnings, Newsletter Topics, Work-Related Links, My X Bookmarks) and saves each collection's raw output to a file, unmodified
2. `scripts/parse_sublime_dump.py` deterministically parses those raw dumps into candidate items (title, source URL, entity type) — no manual transcription, so nothing gets dropped by hand-copying error
3. `scripts/sync_from_dumps.py` dedupes against `library-sync-state.json` (the published dataset, keyed by normalized URL), skips file/PDF cards and title-less highlights, stamps new items with today's date, and re-renders `library.html` as a single flat list sorted newest-first
4. Commits and pushes the update automatically — `library-sync-log.jsonl` gets a run record appended every night (even when nothing's new), so a silent miss can be diagnosed later instead of just noticed

**Files:**
- `scripts/parse_sublime_dump.py` — regex parser for Sublime's `get_collection_items` text output
- `scripts/sync_from_dumps.py` — CLI that ties parsing, deduping, and rendering together
- `scripts/sync_library.py` — shared merge/render/title-reconciliation logic
- `library-sync-state.json` — the full published dataset (title/url/source/date per item)
- `library-sync-log.jsonl` — append-only log of every sync run

**Note:** unlike the Substack sync, this isn't a GitHub Action — it's a scheduled Claude session, since pulling from Sublime requires an MCP connector that a plain Action runner can't reach.

**Excluded from the library page:** file/PDF cards, untitled highlights with no real title or source link, and the Kindle-import and Great Quotes collections.
