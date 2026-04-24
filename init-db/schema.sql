-- Core Email Storage
CREATE TABLE IF NOT EXISTS emails (
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
CREATE TABLE IF NOT EXISTS attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id),
    filename TEXT,
    mime_type TEXT,
    size_bytes BIGINT,
    storage_ref TEXT, 
    extracted_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Operational Cases
CREATE TABLE IF NOT EXISTS bookkeeping_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_email_id UUID REFERENCES emails(id),
    status TEXT DEFAULT 'new',
    request_type TEXT,
    accounting_period TEXT,
    due_at TIMESTAMP WITH TIME ZONE,
    extracted_json JSONB,
    summary_text TEXT,
    confidence FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Match Candidates
CREATE TABLE IF NOT EXISTS candidate_receipts (
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
CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES bookkeeping_cases(id),
    action_type TEXT,
    action_payload_json JSONB,
    status TEXT DEFAULT 'pending',
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE,
    response_text TEXT
);

-- Audit & Traceability
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT,
    entity_id UUID,
    event_type TEXT,
    event_payload_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
