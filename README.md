# hf-trend-snapshots

This repository collects compact weekly snapshots of public Hugging Face model
metadata. It uses the official Hugging Face Hub API, publishes validated
`csv.gz` files as GitHub Release assets, and deploys a static weekly dashboard
to GitHub Pages.

## One-time setup

1. Create a GitHub repository named `hf-trend-snapshots`. The source repository
   may remain private.
2. Upload this folder's contents to the repository root, including `.github`.
3. In repository Settings, open Actions > General and allow workflows to read
   and write repository contents.
4. Optionally add a read-only Hugging Face token as the Actions secret
   `HF_TOKEN`. Public collection also works without it.
5. In Settings > Pages, choose **GitHub Actions** as the publishing source.
6. Open Actions and run `Collect Hugging Face model snapshot` once manually.

The scheduled workflow runs at 00:30 UTC every Monday, which is 08:30 in
Asia/Shanghai. It retains the newest 52 snapshot releases.

The dashboard needs three valid weekly snapshots before its first deployment.
If this repository already has at least three snapshot releases, the next
manual run creates the dashboard immediately. Otherwise, the workflow stores
each weekly release and starts publishing the dashboard after the third one.

To initialize immediately from the existing local compact snapshots, run this
one-time command after authenticating the GitHub CLI. It validates checksums,
schemas, row counts, and duplicate IDs before publishing any asset:

```bash
GH_TOKEN="$(gh auth token)" python scripts/publish_seed_releases.py \
  --repo YOUR_OWNER/hf-trend-snapshots \
  --snapshot-dir "/path/to/Hugging Face/compact_snapshots"
```

Run the collector workflow manually once after the import. Future runs need no
local scripts or terminal commands.

## Dashboard

After a successful run with three snapshots, open the GitHub Pages URL shown in
the `deploy-dashboard` workflow job. The page fetches
`data/hugging-face/latest.json` with browser caching disabled and displays the
latest successful generation time in Asia/Shanghai, summary counts, and a
filterable Top 500 weekly ranking.

GitHub Pages content is publicly accessible even when the repository is
private. Do not add secrets, internal notes, or raw collection data to `site/`.
Only the derived weekly result JSON is deployed.

## Data definitions

- `downloads_all_time`: cumulative downloads since model creation.
- `downloads_30d`: downloads over the most recent 30 days; used only to build
  the candidate pool and to describe new models.
- Weekly downloads are calculated locally from differences between cumulative
  snapshots. This repository does not publish estimated weekly counts.
- The dashboard uses the newest three snapshots, normalizes unequal intervals
  to seven-day equivalents, includes up to 450 complete-history models and 50
  new-model observations, and excludes decreasing cumulative-download values.
