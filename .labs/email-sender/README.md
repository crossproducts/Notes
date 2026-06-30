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
- Replies often arrive from a **different** gateway than you send to — e.g. you
  send to `…@tmomail.net` but a Metro number replies from `+1…@mymetropcs.com`.
  The poller handles this by matching on the bare phone **digits** (found in
  every gateway form), scanning recent unseen mail client-side rather than
  relying on Gmail's IMAP `FROM` search (which tokenizes and misses partials).

## Local-model autoresponder

`autoresponder.py` replies to whitelisted senders automatically, using a **local
Ollama model** (nothing leaves your machine — no API keys). It's the conversation
loop with the human swapped for a model.

```bash
cp whitelist.example.txt whitelist.txt    # add your numbers/emails
ollama pull qwen2.5:3b                     # if not already pulled

python autoresponder.py                    # DRY-RUN: prints proposed replies only
python autoresponder.py --send             # actually replies to whitelisted senders
python autoresponder.py --send --model qwen3:1.7b --once
```

Safety, by design:
- **Dry-run by default** — nothing is sent (and your mailbox isn't marked read)
  until you pass `--send`. Always preview first.
- **Whitelist only** — `whitelist.txt` (gitignored) lists who gets a reply;
  everyone else is ignored. Phone numbers match by digits, emails by address.
- **Loop guard** — skips `no-reply`/`mailer-daemon`/`notification`-type senders
  so it can't ping-pong with another autoresponder.
- Replies go to the sender's **actual** address, so SMS gateway texts return to
  the phone. Replies are capped to ~300 chars for SMS.

Prereqs: IMAP enabled in Gmail; Ollama running (`ollama serve`) with the model pulled.

## Limits

- **Gmail caps total message size at 25 MB.** Beyond that, share a Drive link.
- **Carrier gateways** (`…@tmomail.net`, `…@vtext.com`, etc.) turn media into MMS,
  which carriers limit to ~300 KB–1 MB and frequently mangle. The script warns
  when you attach media to one. Send video to real inboxes.

## Security

- `.env` is gitignored. Never commit the App Password.
- The script reads credentials only from the environment — nothing is hard-coded.
