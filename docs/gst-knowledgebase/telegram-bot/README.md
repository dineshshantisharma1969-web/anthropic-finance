# GST Law Telegram Bot

Ask GST law/rules questions from your phone via Telegram; answers come **only**
from the loaded law library (`../law-library/`), with citations — per the golden
rules in `../SKILL_GST.md`. The bot never answers from AI memory: if the library
doesn't cover a question, it says so and names the official CBIC source to fetch.

## How it works

```
Telegram message
   → keyword retrieval over law-library/ (.md/.txt files)
   → top-4 matching docs sent to Claude (claude-opus-4-8) as
     citation-enabled document blocks
   → Claude reasons ONLY over those docs (system prompt enforces golden rules)
   → cited answer back to Telegram (Position / Basis / Risk / Action format)
```

## Quickest start on Windows

1. Install Python 3.10+ from python.org (tick **"Add python.exe to PATH"**).
2. Get the code:
   ```
   git clone https://github.com/dineshshantisharma1969-web/anthropic-finance.git
   cd anthropic-finance
   git checkout claude/pf-salary-reconciliation-2026-1x7pmd
   ```
   (or download the repo ZIP from GitHub — Code → Download ZIP)
3. Open `docs\gst-knowledgebase\telegram-bot\run_bot.bat` in Notepad, paste your
   two keys, save, double-click it. Done — message your bot on Telegram.

For a Linux server, use `gst-bot.service` (instructions inside the file).

## Setup (one-time, ~10 minutes)

1. **Create the Telegram bot**: open Telegram → search `@BotFather` → `/newbot`
   → pick a name (e.g. *ISPL GST Law Bot*) → copy the token.
2. **Get an Anthropic API key**: console.anthropic.com → API Keys.
3. **Install & run** (any machine with Python 3.10+ that stays on — a laptop,
   office server, or a small cloud VM):

   ```bash
   cd docs/gst-knowledgebase/telegram-bot
   pip install -r requirements.txt
   export TELEGRAM_BOT_TOKEN=...      # from step 1
   export ANTHROPIC_API_KEY=...      # from step 2
   python gst_bot.py
   ```

4. **Load the law library**: put `.md`/`.txt` files (text extracted from
   official CBIC PDFs — cbic-gst.gov.in › GST Law) under
   `docs/gst-knowledgebase/law-library/`. Then send `/reload` to the bot.

## Commands

| Command | Action |
|---|---|
| `/start`, `/help` | usage info |
| `/status` | how many library documents are loaded, and which |
| `/reload` | re-read the law library from disk (after adding new docs) |
| *(any text)* | a GST question — answered with citations from the library |

## Notes

- **Empty library = honest bot.** Until source documents are loaded, the bot
  will answer every legal question with "the library doesn't cover this" — by
  design. Load the CBIC updated Acts/Rules PDFs (as text) first.
- Retrieval is keyword-based (simple, zero dependencies). If the library grows
  large and retrieval quality drops, swap `retrieve()` for embeddings without
  touching the rest of the bot.
- Costs: each question sends ~top-4 doc slices to the API; the system prompt is
  prompt-cached. Typical question ≈ a few cents.
- Keep the bot token and API key out of git — `.env.example` is the template;
  the real `.env` must never be committed.
