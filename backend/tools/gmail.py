import os
import json
import base64
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

TOKEN_DIR = Path(__file__).parent / "gmail_tokens"
TOKEN_DIR.mkdir(exist_ok=True)

# Account registry — maps account key to env var prefixes and token file
ACCOUNTS = {
    "personal": {
        "client_id_env": "GMAIL_PERSONAL_CLIENT_ID",
        "client_secret_env": "GMAIL_PERSONAL_CLIENT_SECRET",
        "token_file": TOKEN_DIR / "personal.json",
    },
    "agaetis": {
        "client_id_env": "GMAIL_AGAETIS_CLIENT_ID",
        "client_secret_env": "GMAIL_AGAETIS_CLIENT_SECRET",
        "token_file": TOKEN_DIR / "agaetis.json",
    },
    "houseofworktops": {
        "client_id_env": "GMAIL_HOUSEOFWORKTOPS_CLIENT_ID",
        "client_secret_env": "GMAIL_HOUSEOFWORKTOPS_CLIENT_SECRET",
        "token_file": TOKEN_DIR / "houseofworktops.json",
    },
}


def _get_service(account: str):
    """Return an authenticated Gmail service for the given account."""
    if account not in ACCOUNTS:
        raise ValueError(f"Unknown account: {account!r}. Valid: {list(ACCOUNTS)}")

    cfg = ACCOUNTS[account]
    token_file: Path = cfg["token_file"]
    client_id = os.getenv(cfg["client_id_env"])
    client_secret = os.getenv(cfg["client_secret_env"])

    if not client_id or not client_secret:
        raise RuntimeError(
            f"Missing env vars for account '{account}': "
            f"{cfg['client_id_env']} and {cfg['client_secret_env']} must be set."
        )

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": ["http://localhost"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def authenticate(account: str):
    """Run the one-time OAuth flow for an account. Call once per account on first setup."""
    _get_service(account)
    print(f"✓ Authenticated: {account} → {ACCOUNTS[account]['token_file']}")


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
    body_preview = _extract_body_preview(msg["payload"])
    return {
        "gmail_id": msg["id"],
        "subject": headers.get("Subject", "(no subject)"),
        "sender": headers.get("From", ""),
        "body_preview": body_preview[:500],
    }


def _extract_body_preview(payload: dict) -> str:
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part["body"].get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
    return ""


def _build_raw_message(to: str, subject: str, body: str) -> str:
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg["to"] = to
    msg["subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()
