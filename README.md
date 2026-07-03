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
