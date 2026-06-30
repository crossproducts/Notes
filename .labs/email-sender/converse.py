#!/usr/bin/env python3
"""Two-way SMS conversation through Gmail (email-to-SMS gateway).

Sends texts to DEFAULT_RECIPIENT (e.g. 3053316270@tmomail.net) and prints the
replies the carrier delivers back into your Gmail inbox. A background thread
polls IMAP for new replies while you type; messages appear as they arrive.

Type a line + Enter to send. /quit (or Ctrl-C) to exit.

Env (.env): GMAIL_ADDRESS, GMAIL_APP_PASSWORD, DEFAULT_RECIPIENT
Prerequisite: enable IMAP in Gmail (Settings -> Forwarding and POP/IMAP).
The same App Password works for IMAP — no new credentials.
"""

import email
import imaplib
import os
import smtplib
import sys
import threading
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
POLL_SECONDS = 10

GMAIL = os.getenv("GMAIL_ADDRESS")
APP_PW = os.getenv("GMAIL_APP_PASSWORD")
PARTNER = os.getenv("DEFAULT_RECIPIENT")

stop = threading.Event()


def send(text):
    """Send one text to the partner gateway address."""
    msg = EmailMessage()
    msg["From"] = GMAIL
    msg["To"] = PARTNER
    msg["Message-ID"] = make_msgid()  # set our own so a future email lab can thread
    msg.set_content(text)
    with smtplib.SMTP_SSL(SMTP_HOST, 465) as s:
        s.login(GMAIL, APP_PW)
        s.send_message(msg)


def body_of(msg):
    """Pull the plain-text body out of a received message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                return payload.decode(errors="replace").strip()
        return ""
    payload = msg.get_payload(decode=True) or b""
    return payload.decode(errors="replace").strip()


def reader():
    """Poll IMAP for unseen replies from the partner and print them."""
    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST)
        imap.login(GMAIL, APP_PW)
    except Exception as e:
        print(f"\n[reader] IMAP login failed: {e}")
        print("[reader] Is IMAP enabled in Gmail settings?")
        stop.set()
        return

    while not stop.is_set():
        try:
            imap.select("INBOX")
            typ, data = imap.search(None, f'(UNSEEN FROM "{PARTNER}")')
            for num in data[0].split():
                typ, raw = imap.fetch(num, "(RFC822)")  # fetch marks it \Seen
                m = email.message_from_bytes(raw[0][1])
                text = body_of(m)
                if text:
                    print(f"\n[{PARTNER}] {text}\n> ", end="", flush=True)
        except Exception as e:
            print(f"\n[reader] poll error: {e}")
        stop.wait(POLL_SECONDS)

    try:
        imap.logout()
    except Exception:
        pass


def main():
    missing = [k for k, v in {
        "GMAIL_ADDRESS": GMAIL,
        "GMAIL_APP_PASSWORD": APP_PW,
        "DEFAULT_RECIPIENT": PARTNER,
    }.items() if not v]
    if missing:
        sys.exit(f"ERROR: missing in .env: {', '.join(missing)}")

    # Windows consoles are cp1252; don't crash if a reply contains an emoji.
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

    print(f"Conversation with {PARTNER}.")
    print(f"Type a message + Enter to send. Replies appear automatically (polled every {POLL_SECONDS}s).")
    print("/quit to exit.\n")

    threading.Thread(target=reader, daemon=True).start()

    try:
        while not stop.is_set():
            line = input("> ")
            if line.strip() in ("/quit", "/exit"):
                break
            if line.strip():
                send(line)
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        stop.set()
    print("\nEnded.")


if __name__ == "__main__":
    main()
