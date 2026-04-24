# Workforce V1: Email-Driven Bookkeeping Assistant

## Overview
A specialized n8n-based automation system designed to reduce bookkeeping friction by detecting missing receipt requests, searching inboxes for matches, and preparing approval-gated responses.

## Tech Stack
- **Orchestration:** n8n
- **Database:** PostgreSQL (for state, audit logs, and matching)
- **Email:** Gmail Node (OAuth2) / IMAP
- **AI:** Gemini 2.0 / OpenAI (Structured extraction and ranking)
- **Notifications:** Telegram / Slack (Approval channel)

## 1. Data Model (PostgreSQL)

```sql
-- Core Email Storage
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mailbox TEXT NOT NULL,
    provider_message_id TEXT UNIQUE NOT NULL,
    thread_id TEXT,
    from_address TEXT,
    subject TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    body_text TEXT,
    snippet TEXT,
    attachment_count INTEGER DEFAULT 0,
    has_attachments BOOLEAN DEFAULT FALSE,
    labels_json JSONB,
    raw_metadata_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attachment Metadata
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id),
    filename TEXT,
    mime_type TEXT,
    size_bytes BIGINT,
    storage_ref TEXT, -- Path to local or cloud storage
    extracted_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Operational Cases
CREATE TABLE bookkeeping_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_email_id UUID REFERENCES emails(id),
    status TEXT DEFAULT 'new', -- new, searching, candidate_found, needs_review, done, blocked
    request_type TEXT, -- missing_receipt, clarification, tax_doc
    accounting_period TEXT,
    due_at TIMESTAMP WITH TIME ZONE,
    extracted_json JSONB,
    summary_text TEXT,
    confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Match Candidates
CREATE TABLE candidate_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES bookkeeping_cases(id),
    email_id UUID REFERENCES emails(id),
    attachment_id UUID REFERENCES attachments(id),
    rank_score FLOAT,
    rank_reason TEXT,
    ai_confidence FLOAT,
    selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Approval Gating
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES bookkeeping_cases(id),
    action_type TEXT, -- draft_reply, notify_user
    action_payload_json JSONB,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE,
    response_text TEXT
);

-- Audit & Traceability
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT,
    entity_id UUID,
    event_type TEXT,
    event_payload_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 2. AI Prompt Contracts

### Task A: Request Extraction
**Goal:** Convert accountant email into structured search parameters.
**Input:** `subject`, `body`, `from_address`.
**Prompt:**
> "Extract bookkeeping requirements from this email. Identify: 
> 1. Period (e.g., 2026-03)
> 2. Required Document (receipt, invoice)
> 3. Vendor hints
> 4. Specific amounts
> Return ONLY JSON: { 'period': string, 'vendor_hints': string[], 'amount_hints': string[], 'urgency': 'high'|'normal' }"

### Task B: Candidate Ranking
**Goal:** Evaluate if a search result matches the request.
**Input:** `Case Summary` + `Candidate Metadata (Subject, Snippet, Date, Attachments)`.
**Prompt:**
> "Compare the missing receipt request [REQUEST] with this candidate email [CANDIDATE]. 
> Provide a confidence score (0-1) and a 1-sentence reason why it matches or fails.
> Return JSON: { 'confidence': float, 'reason': string }"

## 3. Workflow Definitions

### W1: Ingestion & Classification
1. **Trigger:** Gmail New Message (poll 5m).
2. **Action:** Check if sender in `accountant_whitelist` OR body contains `puuttuu`, `kuitti`, `receipt`.
3. **Logic:** If "Bookkeeping Request" -> Save to `emails` -> Trigger W2.
4. **Logic:** If "Possible Receipt" (has attachment + vendor keywords) -> Save to `emails` -> End.

### W2: Case Building
1. **Action:** Call LLM with Extraction Prompt.
2. **Action:** Create `bookkeeping_case` in DB.
3. **Action:** Trigger W3 (Search).

### W3: Receipt Search
1. **Action:** Query `emails` table for `sent_at` within +/- 15 days of `accounting_period`.
2. **Action:** Filter by `vendor_hints` and `has_attachments = true`.
3. **Action:** Rank results using weighted scoring (Date match: 0.3, Vendor match: 0.5, Amount match: 0.2).
4. **Action:** LLM rank top 3 candidates.
5. **Action:** Save to `candidate_receipts`.

### W4: Approval (Telegram)
1. **Action:** Format message: "Found match for [Vendor] in [Account B]. [Reason]. Should I draft a reply?"
2. **Action:** Inline buttons: [Approve], [Reject], [Inspect].
3. **Action:** Wait for webhook response.

## 5. External Integrations

### Python Matcher (`/Users/perttu/projects/kuitit`)
- **Role:** Heavy-lifting extraction and matching logic.
- **n8n Integration:** Use the `Execute Command` node or a local `Python` node to invoke the script on candidate attachments.
- **Input:** File path to the candidate attachment.
- **Output:** Structured JSON with vendor, date, and amount.

### Storage & Sources
- **Scanned Documents:** `/Volumes/nfs/scan/` (mounted from `afp://NAS542`).
- **Archive Destination:** Google Drive Shared Drive `Valkohelmi/kirjanpito`.
- **Workflow Update:** W3 should search both the `emails` table and the local `/Volumes/nfs/scan/` directory for missing documents.

## 6. Updated Workflow Logic

### W3: Receipt Search (Enhanced)
1. **Action:** Query `emails` table.
2. **Action:** List files in `/Volumes/nfs/scan/` filtered by `created_at` proximity.
3. **Action:** Run `/Users/perttu/projects/kuitit/match.py` on top candidates.
4. **Action:** Score and rank results.

### W5: Execution (Enhanced)
1. **Action:** Create Gmail draft (existing).
2. **Action:** Upload the approved receipt to Google Drive `Valkohelmi/kirjanpito/[Period]/`.
3. **Action:** Mark case as done.
