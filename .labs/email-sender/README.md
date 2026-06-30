# Email Sender (Gmail SMTP)

Actually *sends* email (unlike the draft-only Gmail connector), with optional
attachments — video, images, docs.

## Setup

1. Enable **2-Step Verification** on your Google account.
2. Create an **App Password**: Google Account → Security → App passwords.
3. `cp .env.example .env` and paste the 16-char App Password into `.env`.
4. `pip install python-dotenv` (optional — or just export the env vars).

## Usage

```bash
# plain text
python send_email.py --to someone@example.com --subject "Hi" --body "test"

# with attachments
python send_email.py --to me@example.com --body "the clip" --attach clip.mp4 chart.png
```

## Two-way SMS conversation

`converse.py` turns the one-way sender into a back-and-forth **text conversation**
with a phone, through Gmail. When you text the carrier gateway and the phone
replies, the carrier delivers that reply *back into your Gmail inbox* — so a
background IMAP poller can show replies while you type.

```bash
python converse.py        # talks to DEFAULT_RECIPIENT from .env
```

- Type a line + Enter to send; replies print automatically (polled every 10s).
- `/quit` or Ctrl-C to exit.
- **Prerequisite:** enable IMAP in Gmail (Settings → Forwarding and POP/IMAP).
  The same App Password works for IMAP — no new credentials.
- If replies don't appear, check the actual `From:` of the carrier's reply in
  Gmail and confirm it matches `DEFAULT_RECIPIENT` (the poller filters on it).

## Limits

- **Gmail caps total message size at 25 MB.** Beyond that, share a Drive link.
- **Carrier gateways** (`…@tmomail.net`, `…@vtext.com`, etc.) turn media into MMS,
  which carriers limit to ~300 KB–1 MB and frequently mangle. The script warns
  when you attach media to one. Send video to real inboxes.

## Security

- `.env` is gitignored. Never commit the App Password.
- The script reads credentials only from the environment — nothing is hard-coded.
