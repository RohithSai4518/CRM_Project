"""
CRM System - Relational Database Schema Definitions & DDL
Complete enterprise CRM schema with foreign keys and optimized indexes
"""

SCHEMA_DDL = """
-- 1. Users & Authentication
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Sales Representative',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    avatar_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Password Reset Tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    is_used INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_pwd_tokens_lookup ON password_reset_tokens(token, is_used);

-- 2. Accounts (Customers / Organizations)
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    annual_revenue REAL DEFAULT 0.0,
    employee_count INTEGER DEFAULT 0,
    phone TEXT,
    website TEXT,
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_country TEXT,
    tier TEXT DEFAULT 'STANDARD',
    status TEXT DEFAULT 'ACTIVE',
    owner_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_accounts_name ON accounts(name);
CREATE INDEX IF NOT EXISTS idx_accounts_owner ON accounts(owner_id);
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);

-- 3. Customer Notes
CREATE TABLE IF NOT EXISTS customer_notes (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    author_id TEXT,
    note_text TEXT NOT NULL,
    category TEXT DEFAULT 'GENERAL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_cust_notes_acc ON customer_notes(account_id);

-- 4. Customer Attachments
CREATE TABLE IF NOT EXISTS customer_attachments (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    uploaded_by_id TEXT,
    filename TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    file_type TEXT,
    storage_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_cust_attachments_acc ON customer_attachments(account_id);

-- 5. Contacts
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    account_id TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    job_title TEXT,
    department TEXT,
    lead_source TEXT,
    is_primary INTEGER DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_account ON contacts(account_id);

-- 6. Leads
CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    company_name TEXT,
    email TEXT NOT NULL,
    phone TEXT,
    status TEXT DEFAULT 'NEW',
    lead_source TEXT,
    lead_score INTEGER DEFAULT 0,
    estimated_value REAL DEFAULT 0.0,
    assigned_to_id TEXT,
    converted_account_id TEXT,
    converted_contact_id TEXT,
    converted_opportunity_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score);
CREATE INDEX IF NOT EXISTS idx_leads_assigned ON leads(assigned_to_id);

-- 7. Opportunities (Deals / Pipeline)
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    account_id TEXT,
    contact_id TEXT,
    name TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'PROSPECTING',
    amount REAL DEFAULT 0.0,
    win_probability INTEGER DEFAULT 10,
    expected_close_date TEXT,
    actual_close_date TEXT,
    loss_reason TEXT,
    owner_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_opps_stage ON opportunities(stage);
CREATE INDEX IF NOT EXISTS idx_opps_owner ON opportunities(owner_id);
CREATE INDEX IF NOT EXISTS idx_opps_account ON opportunities(account_id);

-- 8. Support Tickets
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    account_id TEXT,
    contact_id TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT DEFAULT 'MEDIUM',
    status TEXT DEFAULT 'OPEN',
    category TEXT DEFAULT 'GENERAL',
    sla_response_deadline TEXT,
    sla_resolution_deadline TEXT,
    sla_response_breached INTEGER DEFAULT 0,
    sla_resolution_breached INTEGER DEFAULT 0,
    assigned_agent_id TEXT,
    csat_score INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_agent_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_agent ON tickets(assigned_agent_id);

-- 9. Ticket Comments / Internal Notes
CREATE TABLE IF NOT EXISTS ticket_comments (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    author_id TEXT,
    comment_text TEXT NOT NULL,
    is_internal INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_ticket_comments_ticket ON ticket_comments(ticket_id);

-- 10. Marketing Campaigns
CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'EMAIL',
    status TEXT DEFAULT 'PLANNING',
    budget REAL DEFAULT 0.0,
    actual_cost REAL DEFAULT 0.0,
    target_audience TEXT,
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    conversion_count INTEGER DEFAULT 0,
    start_date TEXT,
    end_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);

-- 11. Activities, Tasks & Calendar Events
CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    activity_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    description TEXT,
    due_date TEXT,
    status TEXT DEFAULT 'PENDING',
    priority TEXT DEFAULT 'MEDIUM',
    related_to_type TEXT,
    related_to_id TEXT,
    assigned_to_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_activities_due ON activities(due_date);
CREATE INDEX IF NOT EXISTS idx_activities_assigned ON activities(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_activities_related ON activities(related_to_type, related_to_id);

-- 12. Tamper-Evident Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    user_email TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    change_summary TEXT,
    ip_address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);
"""
