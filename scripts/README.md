# Narrative Source Live Development

This is the development copy for source completion, platform monitoring, and alert rules.

## Local Run

```bash
python3 scripts/rebuild_research.py --min-alert-score 60
python3 -m http.server 8781
```

Open `http://127.0.0.1:8781/`.

## What It Builds

- `data/source_research_backlog.csv`: prioritized list of tokens whose source still needs verification.
- `data/launch_platforms.csv`: seed watchlist for primary issuance surfaces such as Four.meme, PancakeSwap SpringBoard, PinkSale, and GemPad.
- `data/alert_candidates.csv`: score-ranked candidates for email review/watchlist.
- `data/state/email_preview.md`: dry-run email body.
- `data/research_status.json`: machine-readable build status.

## Email Later

The script does not send email yet. After the mailbox is provided, fill `.env` from `.env.example`, add SMTP support, and switch `ALERT_DRY_RUN=false`.

