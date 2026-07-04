#!/usr/bin/env python3
"""
GST Law Telegram Bot — answers GST law/rules queries from the law library.

Architecture (per SKILL_GST.md golden rules):
  Telegram message -> retrieve relevant docs from law-library/ -> Claude API
  (claude-opus-4-8) reasons ONLY over retrieved text -> cited answer back.
  The bot never answers from model memory; if the library lacks coverage it
  says so and names the official source to fetch.

Setup:
  1. pip install -r requirements.txt
  2. Get a bot token from @BotFather on Telegram.
  3. export TELEGRAM_BOT_TOKEN=...   and   export ANTHROPIC_API_KEY=...
  4. Put law-library source files (.md/.txt extracted from official CBIC PDFs)
     under the LIBRARY_DIR below (default: ../law-library).
  5. python gst_bot.py
"""
import html
import logging
import math
import os
import re
from pathlib import Path

import anthropic
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger("gst-bot")

LIBRARY_DIR = Path(os.environ.get("GST_LIBRARY_DIR", Path(__file__).parent.parent / "law-library"))
# extra knowledge folders (salary reconciliation summaries etc.) — the bot answers
# ISPL payroll questions from these the same way it answers law from the library
EXTRA_DIRS = [Path(p) for p in os.environ.get(
    "EXTRA_LIBRARY_DIRS",
    str(Path(__file__).parent.parent.parent / "pf-salary-reconciliation")
).split(os.pathsep)]
MODEL = "claude-opus-4-8"
MAX_DOC_CHARS = 60_000          # per retrieved doc slice sent to the model
TOP_K = 4                       # docs per query
HISTORY_TURNS = 6               # remembered turns per chat

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

# --------------------------------------------------------------------------
# System prompt — frozen (cacheable). Encodes SKILL_GST.md golden rules.
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a research assistant answering queries over Telegram for a \
tax/finance professional at ISPL (Impressions Services), covering two domains:
(A) GST (India) law — from the law-library documents; and
(B) ISPL salary/PF/ESI reconciliation data — from the pf-salary-reconciliation \
summary documents (monthly worklists: recovery review, ESI enrollment, wage-code 50%). \
For salary questions, quote the exact figures from those documents and name the month \
and file; if a month's summary is not in the documents, say it has not been examined yet.

GOLDEN RULES — never violated:
1. Answer ONLY from the law-library documents provided in the conversation. \
NEVER answer a legal question from your own memory. If the provided documents \
do not cover the question, say exactly that and name the official source to \
fetch (cbic-gst.gov.in > GST Law section). Partial coverage -> answer the \
covered part, flag the gap.
2. Cite precisely with effective dates: S.16(2)(c) CGST Act (as amended w.e.f. \
01-01-2022) / Rule 36(4) CGST Rules / NN 13/2017-CT(R) dt 28-06-2017 / \
Circular 172/04/2022-GST. Quote operative words verbatim where they decide the issue.
3. Source hierarchy: Act > Rules > Notifications > Orders > Circulars (bind the \
department, not the taxpayer — cite them FOR the taxpayer when favourable) > \
FAQs/portal advisories (no legal force). Case law: SC > jurisdictional HC > \
other HC > AAAR/AAR (AAR binds only the applicant — always flag this).
4. State the relevant tax period — GST provisions change; if the user didn't \
specify a period, note which period your answer assumes.
5. For notices/litigation questions: state the limitation/reply deadline FIRST.

ANSWER FORMAT (Telegram — keep under 3500 characters, plain text, no markdown \
tables; use short lines and simple bullets):
Position: <one-line answer>
Basis: <citations with dates; brief reasoning>
Risk/contrary view: <only if one genuinely exists>
Action: <what to do next, if applicable>

Be direct and practical. If the question is ambiguous, state your assumption \
and answer, rather than only asking a clarifying question."""

# --------------------------------------------------------------------------
# Naive retrieval over the law library (keyword scoring).
# Good enough to start; swap for embeddings later without touching the bot.
# --------------------------------------------------------------------------
def load_library() -> list[tuple[str, str]]:
    docs = []
    roots = [(LIBRARY_DIR, "")] + [(d, f"{d.name}/") for d in EXTRA_DIRS if d.exists()]
    for root, prefix in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            # archive/ holds superseded period-versions (old-period matters only)
            # — excluded so current-period answers never cite stale text
            if "archive" in p.parts:
                continue
            if p.suffix.lower() in (".md", ".txt") and p.is_file():
                try:
                    docs.append((prefix + str(p.relative_to(root)), p.read_text(errors="ignore")))
                except OSError:
                    pass
    log.info("law library: %d documents loaded from %s", len(docs), LIBRARY_DIR)
    return docs

LIBRARY = load_library()

# words too common in a tax statute to discriminate between chapters
STOPWORDS = {"the", "and", "for", "any", "such", "under", "shall", "may", "means",
             "tax", "goods", "services", "service", "supply", "supplies", "person",
             "act", "acts", "rule", "rules", "section", "sections", "gst", "cgst",
             "said", "provided", "where", "with", "that", "this", "not", "central"}

def retrieve(query: str, k: int = TOP_K) -> list[tuple[str, str]]:
    ql = query.lower()
    words = {w for w in re.findall(r"[a-z0-9]+", ql) if len(w) > 2 and w not in STOPWORDS}
    # "section 73" / "rule 36" style references get a heading-level boost
    refs = re.findall(r"(?:section|sec|rule)\s*(\d+[a-z]*)", ql)
    scored = []
    for name, text in LIBRARY:
        tl = text.lower()
        tf = sum(tl.count(w) for w in words)
        score = 1000.0 * tf / math.sqrt(max(1, len(tl)))       # length-normalized
        score += 10 * sum(w in name.lower() for w in words)     # filename hit
        for n in refs:                                          # "73. ..." heading present?
            if re.search(rf"^\s*(?:\d+\[)?{n}\.\s", text, re.M):
                score += 40
        if score > 0:
            scored.append((score, name, text))
    scored.sort(key=lambda s: -s[0])
    return [(n, t[:MAX_DOC_CHARS]) for _, n, t in scored[:k]]

# --------------------------------------------------------------------------
# Claude call
# --------------------------------------------------------------------------
def ask_claude(history: list[dict], question: str) -> str:
    docs = retrieve(question)
    content: list[dict] = []
    for name, text in docs:
        content.append({
            "type": "document",
            "source": {"type": "text", "media_type": "text/plain", "data": text},
            "title": name,
            "citations": {"enabled": True},
        })
    content.append({"type": "text", "text": question if docs else
                    f"{question}\n\n[NOTE: no law-library documents matched this query — "
                    f"follow Golden Rule 1: say the library lacks coverage and name the official source.]"})

    messages = history + [{"role": "user", "content": content}]
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=[{"type": "text", "text": SYSTEM_PROMPT,
                 "cache_control": {"type": "ephemeral"}}],
        messages=messages,
    )
    parts = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
            # append citation markers so the user sees which doc supported it
            for c in (getattr(block, "citations", None) or []):
                title = getattr(c, "document_title", None)
                if title:
                    parts.append(f" [{title}]")
    return "".join(parts).strip() or "No answer produced — please rephrase."

# --------------------------------------------------------------------------
# Telegram handlers
# --------------------------------------------------------------------------
HELP = (
    "GST Law Bot — ask any question on GST law, rules, notifications, returns or cases.\n\n"
    "Answers come ONLY from the loaded law library, with citations. "
    "If the library doesn't cover it, I'll say so.\n\n"
    "Commands:\n/start /help — this message\n/reload — reload the law library\n"
    f"/status — library status\n\nLibrary: {LIBRARY_DIR}"
)

async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP)

async def cmd_status(update: Update, _: ContextTypes.DEFAULT_TYPE):
    names = "\n".join(f"• {n}" for n, _t in LIBRARY[:30]) or "(empty — load official CBIC docs first)"
    await update.message.reply_text(f"Documents loaded: {len(LIBRARY)}\n{names}")

async def cmd_reload(update: Update, _: ContextTypes.DEFAULT_TYPE):
    global LIBRARY
    LIBRARY = load_library()
    await update.message.reply_text(f"Reloaded: {len(LIBRARY)} documents.")

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = (update.message.text or "").strip()
    if not question:
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    history = context.chat_data.setdefault("history", [])
    try:
        answer = ask_claude(history, question)
    except anthropic.APIStatusError as e:
        log.error("API error: %s", e)
        await update.message.reply_text(f"API error ({e.status_code}) — try again shortly.")
        return
    except anthropic.APIConnectionError:
        await update.message.reply_text("Network error reaching the API — try again.")
        return

    # keep short plain-text history (text only — documents are re-retrieved per query)
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    del history[:-2 * HISTORY_TURNS]

    for i in range(0, len(answer), 3800):          # Telegram 4096-char limit
        await update.message.reply_text(answer[i:i + 3800])

def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler(["start", "help"], cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("reload", cmd_reload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    log.info("GST bot running (model=%s, library=%d docs)", MODEL, len(LIBRARY))
    app.run_polling()

if __name__ == "__main__":
    main()
