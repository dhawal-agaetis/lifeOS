import base64
import re
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

TOKEN_DIR = Path(__file__).parent / "gmail_tokens"
TOKEN_DIR.mkdir(exist_ok=True)

# Account registry — token files created by gmail_auth.py
ACCOUNTS = {
    "personal":         {"token_file": TOKEN_DIR / "personal.json"},
    "agaetis":          {"token_file": TOKEN_DIR / "agaetis.json"},
    "houseofworktops":  {"token_file": TOKEN_DIR / "houseofworktops.json"},
}


def _get_service(account: str):
    """Return an authenticated Gmail service for the given account.

    Requires a token file created by gmail_auth.py. Token is refreshed
    automatically when expired — no env vars needed after first auth.
    """
    if account not in ACCOUNTS:
        raise ValueError(f"Unknown account: {account!r}. Valid: {list(ACCOUNTS)}")

    token_file: Path = ACCOUNTS[account]["token_file"]

    if not token_file.exists():
        raise RuntimeError(
            f"No token found for '{account}'. "
            f"Run: cd backend && python tools/gmail_auth.py {account}"
        )

    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_file.write_text(creds.to_json())
        else:
            raise RuntimeError(
                f"Token for '{account}' is invalid and cannot be refreshed. "
                f"Re-run: cd backend && python tools/gmail_auth.py {account}"
            )

    return build("gmail", "v1", credentials=creds)


def load_gmail_service(account: str):
    """Public alias for _get_service — returns authenticated Gmail service object."""
    return _get_service(account)


def is_authenticated(account: str) -> bool:
    """Return True if a valid token already exists for this account."""
    token_file = ACCOUNTS[account]["token_file"]
    if not token_file.exists():
        return False
    try:
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        return creds.valid or bool(creds.refresh_token)
    except Exception:
        return False


def get_unread_emails(account: str, max_results: int = 10) -> list[dict]:
    service = _get_service(account)
    result = service.users().messages().list(
        userId="me",
        labelIds=["UNREAD"],
        maxResults=max_results,
    ).execute()

    messages = result.get("messages", [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        parsed = _parse_message(detail)
        parsed["account"] = account
        emails.append(parsed)

    return emails


def get_recent_emails(account: str, max_results: int = 50) -> list[dict]:
    """Fetch recent emails regardless of read/unread status.

    Preferred over get_unread_emails for high-volume inboxes — read/unread
    status is unreliable as a processing gate (opening an email in Gmail
    removes it from the unread feed). Use DB gmail_id tracking instead.
    """
    service = _get_service(account)
    result = service.users().messages().list(
        userId="me",
        maxResults=max_results,
    ).execute()

    messages = result.get("messages", [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        parsed = _parse_message(detail)
        parsed["account"] = account
        emails.append(parsed)

    return emails


def get_emails_by_subject_pattern(
    account: str, pattern: str, max_results: int = 20
) -> list[dict]:
    """Return emails whose subject contains `pattern` (case-insensitive)."""
    service = _get_service(account)
    result = service.users().messages().list(
        userId="me",
        q=f"subject:{pattern}",
        maxResults=max_results,
    ).execute()

    messages = result.get("messages", [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        parsed = _parse_message(detail)
        parsed["account"] = account
        emails.append(parsed)

    return emails


def get_all_emails_by_subject_pattern(account: str, pattern: str) -> list[dict]:
    """Paginate through all Gmail results matching `pattern` in subject.

    Gmail's maxResults cap is 500 per page; this loops until no nextPageToken.
    Use for backfill / historical fetches where total count is unknown.
    """
    service = _get_service(account)
    message_stubs: list[dict] = []
    page_token: str | None = None

    while True:
        kwargs: dict = {"userId": "me", "q": f"subject:{pattern}", "maxResults": 500}
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.users().messages().list(**kwargs).execute()
        message_stubs.extend(result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    emails = []
    for msg in message_stubs:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        parsed = _parse_message(detail)
        parsed["account"] = account
        emails.append(parsed)

    return emails


def mark_as_read(account: str, email_id: str) -> bool:
    service = _get_service(account)
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()
    return True


def send_email(account: str, to: str, subject: str, body: str) -> bool:
    service = _get_service(account)
    raw = _build_raw_message(to, subject, body)
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return True


def _parse_message(msg: dict) -> dict:
    headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
    full_body = _extract_body(msg["payload"])
    return {
        "id": msg["id"],
        "gmail_id": msg["id"],
        "subject": headers.get("Subject", "(no subject)"),
        "sender": headers.get("From", ""),
        "date": headers.get("Date", ""),
        "snippet": msg.get("snippet", ""),
        "body_preview": full_body[:500],
        "full_body": full_body,
    }


def _extract_body(payload: dict) -> str:
    plain = _extract_mime(payload, "text/plain")
    # Many HoW emails are HTML-only; the text/plain part is a stub fallback message.
    # Fall back to stripped HTML when text/plain is too short to contain order data.
    if len(plain) >= 200:
        return plain
    html = _extract_mime(payload, "text/html")
    if html:
        return _strip_html(html)
    return plain


def _extract_mime(payload: dict, mime: str) -> str:
    """Recursively find the first part matching `mime` and decode its body."""
    if "body" in payload and payload["body"].get("data") and not payload.get("parts"):
        # Simple (non-multipart) message — return regardless of mime type
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    for part in payload.get("parts", []):
        if part.get("mimeType") == mime and part["body"].get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
        if part.get("mimeType", "").startswith("multipart"):
            result = _extract_mime(part, mime)
            if result:
                return result
    return ""


def _strip_html(html: str) -> str:
    """Strip HTML tags and decode common entities — good enough for structured order emails."""
    import html as html_module
    text = re.sub(r"<[^>]+>", " ", html)
    text = html_module.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\xa0]+", " ", text)  # collapse whitespace + non-breaking spaces
    text = re.sub(r" *\n *", "\n", text)      # strip spaces around newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_raw_message(to: str, subject: str, body: str) -> str:
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()
