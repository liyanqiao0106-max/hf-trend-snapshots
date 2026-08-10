# hf-trend-snapshots

This repository collects compact weekly snapshots of public Hugging Face model
metadata. It uses the official Hugging Face Hub API and publishes validated
`csv.gz` files as GitHub Release assets.

## One-time setup

1. Create a public GitHub repository named `hf-trend-snapshots`.
2. Upload this folder's contents to the repository root, including `.github`.
3. In repository Settings, open Actions > General and allow workflows to read
   and write repository contents.
4. Optionally add a read-only Hugging Face token as the Actions secret
   `HF_TOKEN`. Public collection also works without it.
5. Open Actions and run `Collect Hugging Face model snapshot` once manually.

The scheduled workflow runs at 00:30 UTC every Monday, which is 08:30 in
Asia/Shanghai. It retains the newest 16 snapshot releases.

## Data definitions

- `downloads_all_time`: cumulative downloads since model creation.
- `downloads_30d`: downloads over the most recent 30 days; used only to build
  the candidate pool and to describe new models.
- Weekly downloads are calculated locally from differences between cumulative
  snapshots. This repository does not publish estimated weekly counts.

