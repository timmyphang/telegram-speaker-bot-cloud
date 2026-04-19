# Telegram Speaker Bot - Cloud Migration Progress

## Status: COMPLETE - Bot Running via Systemd (2026-04-20)

## What We're Doing
Moved Telegram speaker bot from Mac to GCP VM, using Google Assistant SDK to broadcast TTS to Google Home via the cloud (no local network needed).

## Architecture
```
Telegram → Bot (GCP VM) → Brave Search + Azure GPT-4o-mini → text
                                                                 ↓
                                                 Google Assistant SDK (broadcast)
                                                                 ↓
                                                 Google Cloud → Google Home Speaker
```

## Accounts
- GCP project owner: tpsntest2026@gmail.com
- Google Home account: timphang@gmail.com (OAuth done under this)
- New Telegram bot: @TimGCPgptbot (token: 8321687813:AAGyem8F4xBzx4Jpm9ljISkSazPshgbap7g)
- Google Cloud project (timphang@gmail.com): tim-gcloud-vm-20260419
- Azure + Brave keys: reused from existing .env

## Existing Bot (DO NOT MODIFY)
- Location: /Users/timphang/telegram-speaker-bot/
- Old Telegram bot token: 8365241300:AAGT-5YE9BFvMHBCFmi40u81sG4LrrK-JzA

## New VM Info
- **Name:** telegram-speaker-bot
- **Zone:** us-central1-a (Always Free tier)
- **Machine type:** e2-micro
- **External IP:** 34.72.17.33
- **Project dir:** ~/telegram-speaker-bot-cloud/

## Device Registration (Google Assistant SDK)
- Device Model ID: tim-gcloud-vm-20260419-speaker-bot-v1
- Device ID: speaker-bot-device-1
- Project: tim-gcloud-vm-20260419

## All Steps Complete
- [x] Create e2-micro VM in us-central1-a
- [x] Set up Python venv + dependencies
- [x] Google Cloud OAuth (timphang@gmail.com) - credentials.json on VM
- [x] Register device model + device instance
- [x] Deploy bot.py, google_broadcast.py, .env
- [x] Test broadcast standalone - SUCCESS
- [x] Bot running and replying to Telegram messages
- [x] Text length fix (chunk messages to ~200 chars)
- [x] Metric system instruction added to prompt
- [x] Bot restarted with all fixes
- [x] Systemd service installed, enabled, auto-starts on boot

## VM Connection (for Claude Code)
```bash
GCLOUD="/Users/timphang/Downloads/google-cloud-sdk/bin/gcloud"
$GCLOUD compute ssh telegram-speaker-bot --zone us-central1-a --project polar-reef-486402-q3 --tunnel-through-iap --force-key-file-overwrite --ssh-key-file ~/.ssh/google_compute_engine_ed25519 --ssh-flag="-o StrictHostKeyChecking=no" --command "COMMAND"
```

## VM Connection (for user in terminal - interactive)
```bash
/Users/timphang/Downloads/google-cloud-sdk/bin/gcloud compute ssh telegram-speaker-bot --zone us-central1-a --project polar-reef-486402-q3
```

## Useful Commands
- Check status: `sudo systemctl status telegram-speaker-bot`
- View logs: `sudo journalctl -u telegram-speaker-bot -f`
- Restart: `sudo systemctl restart telegram-speaker-bot`
- Stop: `sudo systemctl stop telegram-speaker-bot`

## Key Notes
- Google Assistant SDK: Free, 500 queries/day
- GCP e2-micro in US: Always Free tier
- No Mac, Home Assistant, or MQTT needed
- PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python is set in bot.py
- credentials.json auto-refreshes via refresh_token
- Broadcast text limit: ~200 chars per request (split into chunks)
- GPT-4o mini prompt includes metric system instruction: Use km/kg/Celsius not miles/pounds/Fahrenheit
- Systemd service auto-restarts on crash (10s delay) and auto-starts on VM boot
