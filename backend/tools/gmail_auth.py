"""
One-time OAuth setup for a Gmail account.
Usage: python tools/gmail_auth.py houseofworktops
"""
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

VALID_ACCOUNTS = ["personal", "agaetis", "houseofworktops"]
TOKEN_DIR = Path(__file__).parent / "gmail_tokens"


def run_auth(account: str) -> None:
    if account not in VALID_ACCOUNTS:
        print(f"Unknown account '{account}'. Valid: {VALID_ACCOUNTS}")
        sys.exit(1)

    TOKEN_DIR.mkdir(exist_ok=True)
    token_file = TOKEN_DIR / f"{account}.json"

    credentials_path = input(
        f"\nPaste the full path to your {account} OAuth credentials JSON file:\n> "
    ).strip().strip("'\"")

    creds_file = Path(credentials_path)
    if not creds_file.exists():
        print(f"File not found: {credentials_path}")
        sys.exit(1)

    print("\nOpening browser for Google login — log in and click Allow...")
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
    creds = flow.run_local_server(port=0)

    token_file.write_text(creds.to_json())
    print(f"\n✓ Token saved to {token_file}")
    print(f"  Do not commit this file — it is gitignored.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/gmail_auth.py <account>")
        print(f"       account must be one of: {VALID_ACCOUNTS}")
        sys.exit(1)

    run_auth(sys.argv[1])
