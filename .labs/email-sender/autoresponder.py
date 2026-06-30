#!/usr/bin/env python3
"""Local-model autoresponder for email/SMS via Gmail.

Polls Gmail for new messages from whitelisted senders (whitelist.txt), generates
a reply with a LOCAL Ollama model (nothing leaves your machine), and replies to
the sender's actual address — so SMS gateway texts go back to the phone.

SAFE BY DEFAULT: dry-run unless you pass --send. In dry-run it prints the reply
it *would* send and does not touch your mailbox or text anyone.

    python autoresponder.py            # dry-run: show proposed replies
    python autoresponder.py --send     # actually reply to whitelisted senders
    python autoresponder.py --send --model qwen3:1.7b

Env (.env): GMAIL_ADDRESS, GMAIL_APP_PASSWORD
Prereqs: IMAP enabled in Gmail; Ollama running with the chosen model pulled.
"""

import argparse
import email
import imaplib
import json
import re
import smtplib
import sys
import time
import urllib.error
import urllib.request
from email.message import EmailMessage
from email.utils import make_msgid, parseaddr
from pathlib import Path

# Reuse the proven helpers/credentials from converse.py
import converse

HERE = Path(__file__).parent
WHITELIST_FILE = HERE / "whitelist.txt"
OLLAMA_URL = "http://localhost:11434/api/chat"
POLL_SECONDS = 10
SCAN_WINDOW = 25            # keep to last 25 unseen, per your call
MAX_REPLY_CHARS = 300      # SMS-friendly cap
SYSTEM_PROMPT = (
    "You are an automated assistant replying to the owner's text messages. "
    "Reply in one or two short, friendly sentences under 300 characters. "
    "Plain text only — no markdown, no preamble."
)

# Never auto-reply to automated senders (loop / bounce protection)
SKIP_PATTERNS = ("no-reply", "noreply", "donotreply", "do-not-reply",
                 "mailer-daemon", "postmaster", "notification")


def load_whitelist():
    """Return (phone_digit_entries, email_entries) from whitelist.txt."""
    phones, emails = [], []
    if not WHITELIST_FILE.exists():
        sys.exit(f"ERROR: {WHITELIST_FILE.name} not found.")
    for line in WHITELIST_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "@" in line:
            emails.append(line.lower())
        else:
            digits = re.sub(r"\D", "", line)
            if digits:
                phones.append(digits)
    return phones, emails


def whitelisted(from_header, phones, emails):
    """Is this sender allowed? Returns the matched key, or None."""
    fl = from_header.lower()
    if any(p in fl for p in SKIP_PATTERNS):
        return None
    addr = parseaddr(from_header)[1].lower()
    for e in emails:
        if e in addr:
            return e
    from_digits = re.sub(r"\D", "", addr)
    for p in phones:
        if p and p in from_digits:
            return p
    return None


def generate_reply(model, incoming):
    """Ask the local Ollama model for a reply. Returns text or None on failure."""
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": incoming},
        ],
        "stream": False,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        text = data.get("message", {}).get("content", "").strip()
        return text[:MAX_REPLY_CHARS] if text else None
    except urllib.error.URLError as e:
        print(f"  [ollama] not reachable ({e}). Is `ollama serve` running and '{model}' pulled?")
        return None


def send(gmail, app_pw, to_addr, text):
    msg = EmailMessage()
    msg["From"] = gmail
    msg["To"] = to_addr
    msg["Message-ID"] = make_msgid()
    msg.set_content(text)
    with smtplib.SMTP_SSL(converse.SMTP_HOST, 465) as s:
        s.login(gmail, app_pw)
        s.send_message(msg)


def run_once(model, do_send, phones, emails):
    """One scan: reply to (or preview) each new whitelisted message."""
    imap = imaplib.IMAP4_SSL(converse.IMAP_HOST)
    imap.login(converse.GMAIL, converse.APP_PW)
    imap.select("INBOX")
    typ, data = imap.search(None, "UNSEEN")
    handled = 0
    for num in data[0].split()[-SCAN_WINDOW:]:
        typ, raw = imap.fetch(num, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
        from_header = raw[0][1].decode(errors="replace") if raw and raw[0] else ""
        if not whitelisted(from_header, phones, emails):
            continue

        # Peek the full message (don't mark seen yet in dry-run)
        fetch_spec = "(RFC822)" if do_send else "(BODY.PEEK[])"
        typ, full = imap.fetch(num, fetch_spec)
        m = email.message_from_bytes(full[0][1])
        incoming = converse.body_of(m)
        if not incoming:
            continue
        sender = parseaddr(from_header)[1]
        print(f"\nFrom {sender}: {incoming!r}")

        reply = generate_reply(model, incoming)
        if not reply:
            print("  (no reply generated; skipping)")
            continue

        if do_send:
            send(converse.GMAIL, converse.APP_PW, sender, reply)
            print(f"  SENT -> {sender}: {reply!r}")
        else:
            print(f"  [dry-run] would send: {reply!r}")
        handled += 1

    imap.logout()
    return handled


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--send", action="store_true", help="actually send replies (default: dry-run preview)")
    ap.add_argument("--model", default="qwen2.5:3b", help="Ollama model (default: qwen2.5:3b)")
    ap.add_argument("--once", action="store_true", help="scan once and exit instead of looping")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

    if not (converse.GMAIL and converse.APP_PW):
        sys.exit("ERROR: set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env.")

    phones, emails = load_whitelist()
    mode = "SEND" if args.send else "DRY-RUN (no messages sent)"
    print(f"Autoresponder [{mode}] model={args.model}")
    print(f"Whitelist: {len(phones)} phone(s), {len(emails)} email(s). Scanning last {SCAN_WINDOW} unseen every {POLL_SECONDS}s.")
    if not args.send:
        print("Pass --send to actually reply.")

    try:
        while True:
            try:
                run_once(args.model, args.send, phones, emails)
            except Exception as e:
                print(f"[poll error] {e}")
            if args.once:
                break
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
