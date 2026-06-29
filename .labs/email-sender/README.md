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

## Limits

- **Gmail caps total message size at 25 MB.** Beyond that, share a Drive link.
- **Carrier gateways** (`…@tmomail.net`, `…@vtext.com`, etc.) turn media into MMS,
  which carriers limit to ~300 KB–1 MB and frequently mangle. The script warns
  when you attach media to one. Send video to real inboxes.

## Security

- `.env` is gitignored. Never commit the App Password.
- The script reads credentials only from the environment — nothing is hard-coded.
