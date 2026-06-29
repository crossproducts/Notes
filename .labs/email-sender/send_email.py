#!/usr/bin/env python3
"""Send email via Gmail SMTP, with optional attachments (video, images, docs).

Credentials come from environment / .env — never hard-code them:
    GMAIL_ADDRESS=you@gmail.com
    GMAIL_APP_PASSWORD=<16-char Google App Password>   # NOT your login password

Usage:
    python send_email.py --to someone@example.com --subject "Hi" --body "test"
    python send_email.py --to a@x.com b@y.com --body "report" --attach clip.mp4 chart.png

Notes:
- Gmail caps total message size at 25 MB. Larger -> share a Drive link instead.
- Sending to a carrier gateway (e.g. ...@tmomail.net) turns media into MMS,
  which carriers limit to ~300 KB-1 MB and often mangle. Use real inboxes for video.
"""

import argparse
import mimetypes
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv optional; env vars may already be set

MAX_BYTES = 25 * 1024 * 1024  # Gmail's 25 MB limit


def build_message(sender, to, subject, body, attachments):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(body)

    total = 0
    for path in attachments:
        p = Path(path)
        if not p.exists():
            sys.exit(f"ERROR: attachment not found: {p}")
        data = p.read_bytes()
        total += len(data)
        ctype, _ = mimetypes.guess_type(p.name)
        maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=p.name)

    if total > MAX_BYTES:
        sys.exit(f"ERROR: attachments total {total/1e6:.1f} MB, exceeds Gmail's 25 MB limit. "
                 "Share a Drive link instead.")
    return msg


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default_to = os.getenv("DEFAULT_RECIPIENT")
    ap.add_argument("--to", nargs="+", default=[default_to] if default_to else None,
                    help="recipient address(es); defaults to DEFAULT_RECIPIENT from .env")
    ap.add_argument("--subject", default="", help="subject line")
    ap.add_argument("--body", default="", help="plain-text body")
    ap.add_argument("--attach", nargs="*", default=[], help="file path(s) to attach")
    args = ap.parse_args()

    if not args.to:
        sys.exit("ERROR: no recipient — pass --to or set DEFAULT_RECIPIENT in .env.")

    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not sender or not password:
        sys.exit("ERROR: set GMAIL_ADDRESS and GMAIL_APP_PASSWORD (in .env or environment).")

    # Carrier-gateway sanity check
    if args.attach and any(r.endswith(("tmomail.net", "vtext.com", "txt.att.net", "messaging.sprintpcs.com"))
                           for r in args.to):
        print("WARNING: a recipient is a carrier SMS/MMS gateway — video/large media will likely "
              "fail or arrive mangled. Send media to a real inbox instead.")

    msg = build_message(sender, args.to, args.subject, args.body, args.attach)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, password)
        s.send_message(msg)

    print(f"Sent to {', '.join(args.to)}" + (f" with {len(args.attach)} attachment(s)" if args.attach else ""))


if __name__ == "__main__":
    main()
