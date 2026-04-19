#!/usr/bin/env python3
"""One-shot OAuth flow: generates URL, waits for code, saves credentials."""
import os, json
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from google_auth_oauthlib.flow import InstalledAppFlow

with open('/Users/timphang/Downloads/client_secret_141102319814-iud8vajcevg94491p7jl8rq590iq946j.apps.googleusercontent.com.json') as f:
    client_config = json.load(f)

flow = InstalledAppFlow.from_client_config(
    client_config,
    scopes=['https://www.googleapis.com/auth/assistant-sdk-prototype'],
    redirect_uri='http://localhost'
)

auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
print("VISIT_THIS_URL:")
print(auth_url)
print(":END_URL")

redirect_url = input("Paste the full redirect URL here: ")
flow.fetch_token(authorization_response=redirect_url)

creds = flow.credentials
with open('/Users/timphang/.claude-glm/workspace/credentials.json', 'w') as f:
    f.write(creds.to_json())
print("SUCCESS - credentials saved")
