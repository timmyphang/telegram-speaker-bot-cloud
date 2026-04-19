#!/usr/bin/env python3
"""One-time OAuth setup: generates credentials.json for Google Assistant SDK."""
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPE = ["https://www.googleapis.com/auth/assistant-sdk-prototype"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET = os.path.join(BASE_DIR, "client_secret.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, scopes=SCOPE)

# Print the URL for manual auth
auth_url, _ = flow.authorization_url(prompt="consent")
print("\n" + "=" * 80)
print("Visit this URL in your browser (logged in as timphang@gmail.com):")
print("=" * 80)
print(auth_url)
print("=" * 80)
code = input("\nEnter the authorization code from the redirect URL: ")
flow.fetch_token(code=code)

creds = flow.credentials
with open(CREDENTIALS_FILE, "w") as f:
    f.write(creds.to_json())

print(f"\nCredentials saved to {CREDENTIALS_FILE}")
print("Setup complete! You can now run bot.py")
