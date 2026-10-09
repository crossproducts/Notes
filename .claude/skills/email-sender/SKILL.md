---
name: email-sender
description: Send real email (with attachments) via Gmail SMTP, hold a two-way SMS conversation through carrier gateways, or run a whitelist-only local-model autoresponder. Use when the user wants to actually send mail/SMS (not just draft it), text a phone via Gmail, or auto-reply to messages. Lives in .labs/email-sender/.
---

# Email Sender

Standalone CLI in `.labs/email-sender/`. It actually **sends** email over Gmail
SMTP (unlike the draft-only Gmail connector), and can attach media/docs.

## Prerequisites
- `.env` in `.labs/email-sender/` holds `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`,
  and optionally `DEFAULT_RECIPIENT`. It is gitignored — never print or commit it.
- Credentials come only from the environment; nothing is hard-coded. The
  `GMAIL_APP_PASSWORD` is a 16-char Google App Password (needs 2-Step Verification).
- For `converse.py` / `autoresponder.py`: IMAP must be enabled in Gmail.

Run everything from `.labs/email-sender/`.

## send_email.py — one-shot send
```bash
python send_email.py --to someone@example.com --subject "Hi" --body "test"
python send_email.py --to me@example.com --body "the clip" --attach clip.mp4 chart.png
```
- `--to` takes one or more addresses (defaults to `DEFAULT_RECIPIENT` if set).
- `--attach` takes one or more file paths.

## converse.py — two-way SMS through Gmail
```bash
python converse.py    # talks to DEFAULT_RECIPIENT from .env
```
Interactive: type a line + Enter to send; replies print (polled ~10s); `/quit`
or Ctrl-C exits. Replies often arrive from a **different** gateway than you sent
to, so the poller matches on the bare phone digits. This is a long-running
interactive process — start it for the user rather than expecting a clean return.

## autoresponder.py — local-model auto-replies (Ollama)
```bash
python autoresponder.py                       # DRY-RUN: prints proposed replies only
python autoresponder.py --send                # actually replies to whitelisted senders
python autoresponder.py --send --model qwen3:1.7b --once
```
Flags: `--send` (default is dry-run), `--model` (default `qwen2.5:3b`),
`--once` (scan once instead of looping). Requires `ollama serve` running with
the model pulled.

## Safety rules — do not violate
- **Sending mail/SMS is outward-facing.** Confirm recipient, subject, and body
  with the user before an actual send unless they've clearly authorized it.
- **autoresponder defaults to dry-run.** Never add `--send` unless the user
  explicitly asks to send for real. Always preview the dry-run output first.
- **Whitelist only.** `autoresponder.py` replies only to entries in
  `whitelist.txt` (gitignored); don't broaden it without being asked.
- Gmail caps total message size at **25 MB**; carrier gateways mangle media —
  send video to real inboxes, not `…@tmomail.net`-style addresses.

## Voice notes (MMS)

`send_voice.py` speaks text and delivers it as a playable voice note on the
phone - same gateway trick, but an attachment makes it an MMS, and iOS plays
`.m4a` inline.

```bash
python send_voice.py --text "Backtest finished. The gate failed, 0 for 10."
python send_voice.py --text "hi" --keep out.m4a --dry-run
```

AAC-LC mono @ 24 kHz, ~4 KB/sec, so ~2-3 minutes fits an MMS. Over budget it
steps the bitrate down then refuses rather than letting the carrier mangle it.
Engines: `--engine piper` / `sapi` are fully local; `edge` (default) is neural
but **sends the text to a Microsoft endpoint**.
