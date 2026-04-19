#!/usr/bin/env python3
"""Google Assistant SDK broadcast helper.
Sends a broadcast message to Google Home speakers via Google's cloud API.
No local network access needed.
"""

import json
import os
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import grpc
from google.assistant.embedded.v1alpha2 import embedded_assistant_pb2
from google.assistant.embedded.v1alpha2 import embedded_assistant_pb2_grpc

SCOPE = ["https://www.googleapis.com/auth/assistant-sdk-prototype"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json")
ASSISTANT_API_ENDPOINT = "embeddedassistant.googleapis.com"


def get_credentials():
    """Load or create OAuth credentials."""
    creds = None
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPE)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(google.auth.transport.requests.Request())
        with open(CREDENTIALS_FILE, "w") as f:
            f.write(creds.to_json())
        return creds
    # Need to run OAuth flow
    if os.path.exists(CLIENT_SECRET_FILE):
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=SCOPE)
        creds = flow.run_console()
        with open(CREDENTIALS_FILE, "w") as f:
            f.write(creds.to_json())
        return creds
    raise FileNotFoundError(
        "No valid credentials found. Run google-oauthlib-tool first, "
        "or place client_secret.json in the project directory."
    )


def _send_broadcast(stub, creds, text):
    """Send a single broadcast request to Google Assistant API."""
    def request_stream():
        yield embedded_assistant_pb2.AssistRequest(
            config=embedded_assistant_pb2.AssistConfig(
                audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                    encoding="LINEAR16",
                    sample_rate_hertz=16000,
                    volume_percentage=100,
                ),
                dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                    language_code="en-US",
                ),
                device_config=embedded_assistant_pb2.DeviceConfig(
                    device_id="speaker-bot-device-1",
                    device_model_id="tim-gcloud-vm-20260419-speaker-bot-v1",
                ),
                text_query=f"Broadcast {text}",
            )
        )

    for response in stub.Assist(
        request_stream(),
        metadata=[("authorization", f"Bearer {creds.token}")],
    ):
        pass  # consume responses


def broadcast_to_google_home(message):
    """Send a broadcast message to Google Home via Google Assistant API.
    Splits long messages into chunks to avoid text_query too long error."""
    creds = get_credentials()

    channel = grpc.secure_channel(
        ASSISTANT_API_ENDPOINT,
        grpc.ssl_channel_credentials()
    )
    stub = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(channel)

    try:
        # Split message into chunks of ~200 chars at sentence/word boundaries
        MAX_CHUNK = 200
        if len(message) <= MAX_CHUNK:
            chunks = [message]
        else:
            chunks = []
            remaining = message
            while remaining:
                if len(remaining) <= MAX_CHUNK:
                    chunks.append(remaining)
                    break
                # Try to split at sentence boundary
                split_at = remaining[:MAX_CHUNK].rfind(". ")
                if split_at == -1:
                    split_at = remaining[:MAX_CHUNK].rfind(" ")
                if split_at == -1:
                    split_at = MAX_CHUNK
                chunks.append(remaining[:split_at + 1].strip())
                remaining = remaining[split_at + 1:].strip()

        for i, chunk in enumerate(chunks):
            try:
                _send_broadcast(stub, creds, chunk)
                print(f"Broadcast chunk {i+1}/{len(chunks)}: {chunk[:60]}...")
            except grpc.RpcError as e:
                print(f"gRPC error on chunk {i+1}: {e.code()} - {e.details()}")
                return False
            import time
            if i < len(chunks) - 1:
                time.sleep(8)  # wait for previous broadcast to finish speaking

        print(f"Broadcast complete ({len(chunks)} chunk(s))")
        return True
    finally:
        channel.close()


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "Hello from the cloud"
    success = broadcast_to_google_home(text)
    print("Success!" if success else "Failed!")
