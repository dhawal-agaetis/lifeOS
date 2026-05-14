import base64
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
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part["body"].get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
        # recurse into multipart
        if part.get("mimeType", "").startswith("multipart"):
            result = _extract_body(part)
            if result:
                return result
    return ""


def _build_raw_message(to: str, subject: str, body: str) -> str:
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()
