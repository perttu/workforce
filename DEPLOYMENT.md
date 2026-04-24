# Workforce V1: Integration & Deployment Guide

This guide details how to bridge the n8n orchestration layer with your local Python matching script and network storage.

## 1. Environment Finalization

Ensure your `.env` file includes the Google Drive and Telegram credentials:
```bash
# Google Drive
GOOGLE_DRIVE_SHARED_DRIVE_ID= # Found in URL of the Valkohelmi/kirjanpito folder
# n8n
N8N_BLOCK_SVC_REGISTRATION_EMAIL=true
```

## 2. Connecting the Python Matcher

Since n8n runs in Docker, you have two options to run your `/opt/kuitit/match.py`:

### Option A: Run inside n8n (Recommended for simplicity)
Update your `docker-compose.yml` to use a custom image if you need specific Python libs, or simply install them on startup:
```yaml
# Add to n8n environment in docker-compose.yml
NODE_FUNCTION_ALLOW_EXTERNAL=path,fs,child_process
```
In n8n, use an **Execute Command** node:
- **Command:** `python3 /opt/kuitit/match.py --json "{{ $json.filePath }}"`

### Option B: Run on Host (Recommended if script has complex dependencies)
Use n8n's **SSH Node** to connect back to your Mac (`localhost` or host IP) and execute the script in its native environment.

## 3. Storage Mapping

The following paths are now standardized across the system:
- **Scan Input:** `/mnt/scan` (Internal to n8n) -> Maps to `/Volumes/nfs/scan/` (Physical NAS).
- **Python Project:** `/opt/kuitit` (Internal to n8n) -> Maps to `/Users/perttu/projects/kuitit`.
- **Archive Target:** Use the n8n **Google Drive Node** with "Shared Drive" support.

## 4. Implementation Checklist

1. **DB Setup:**
   - [ ] Run `docker-compose up -d`.
   - [ ] Verify tables exist: `docker exec -it workforce-db psql -U workforce -d workforce -c "\dt"`.

2. **n8n Credentialing:**
   - [ ] **Gmail:** Set up OAuth2 (requires Google Cloud Console project).
   - [ ] **Google Drive:** Use same GCP project as Gmail.
   - [ ] **Telegram:** Create bot via BotFather and get `chat_id`.

3. **Workflow Import:**
   - [ ] Import `workflows/w1_ingestion.json` -> Connect Gmail.
   - [ ] Import `workflows/w2_case_builder.json` -> Connect LLM (Gemini/OpenAI).
   - [ ] Import `workflows/w3_search.json` -> Point to `/mnt/scan` and `emails` table.
   - [ ] Import `workflows/w4_approval.json` -> Connect Telegram.
   - [ ] Import `workflows/w5_execution.json` -> Connect Google Drive (Valkohelmi/kirjanpito).

## 5. First Test Run
1. Send an email to yourself: "Subject: Missing Amazon receipt for 2026-03".
2. Wait 1 min for W1 to trigger.
3. Check Telegram for the match notification.
4. Click "Approve" and verify the draft in Gmail and the file in Google Drive.
