# BSC Four.meme Narrative Source & Signal Model

[中文](README.md) | English

This is a new project split from the original onchain review. The original repository `hahahakang/bsc-fourmeme-analysis` keeps the article and trader reconstruction; this repository carries the follow-up work: tracing the earliest narrative source for each token, identifying strongly related information sources, measuring post-entry fermentation windows, and turning the findings into reusable signal rules for a BSC meme-token research bot.

Public website:

https://hahahakang.github.io/bsc-fourmeme-narrative-source-analysis/

## Chinese First, English Switchable

The website opens in Chinese by default. The `English` button switches the page into English for public collaboration, external sharing, and data explanation.

## What This Project Answers

- Where each token's first story came from: a person, company, project, official feature, media IP, Chinese social meme, or celebrity-name token.
- Which sources are strongly related to the project: founder posts, official announcements, product launches, company leader updates, supply-chain figures, and similar origin events.
- How long the story needs to ferment after entry: win rate, realized PnL, and FDV bucket performance by holding or exit window.
- What should be accumulated for future bots: source strength, time advantage, leader/copycat status, FDV/liquidity, and risk penalties.
- Why this should not be fully automated yet: the current stage is an information radar plus human confirmation, not a single-case certainty machine.

## Current Additions

- First narrative source timeline: candidate origin event, evidence grade, entry-vs-source window, relationship strength, and bot implications.
- Source library: people, companies, projects, official accounts, media IP, Chinese short-video memes, and analogous offchain cases such as Jensen Huang or Marvell-style market narratives.
- Narrative candidate pool: token name, description, narrative tag, guessed source type, evidence status, and research priority.
- Fermentation window statistics: holding/exit window, win rate, realized PnL, FDV, and liquidity.
- FDV bucket x holding window matrix: which entry node and waiting window historically worked better.
- Signal model draft: source quality, time advantage, onchain quality, liquidity execution, and risk penalty.

## Data Files

- `data/source_timeline_research.csv`
- `data/source_library.csv`
- `data/narrative_candidates.csv`
- `data/fermentation_window_summary.csv`
- `data/bucket_window_summary.csv`
- `data/source_signal_model.csv`
- `data/token_trade_summary_with_windows.csv`
- `data/buy_detail_with_fdv.csv`
- `data/fdv_bucket_summary.csv`
- `data/top_winners.csv`
- `data/top_losers.csv`

## Method Notes

The onchain trade reconstruction and window statistics come from locally decoded data. Narrative source grades are evidence grades, not buy ratings: A means primary or official source; B means strong secondary source with original-post context; C means token or project-page attribution; D means retrospective community explanation; E means no source matched yet. This project is research only and is not investment advice.
