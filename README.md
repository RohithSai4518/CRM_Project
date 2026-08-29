# OmniFlow CRM - Enterprise Customer Relationship Management Platform

An enterprise-grade, high-performance Customer Relationship Management (CRM) system engineered with clean domain-driven architecture, modular service subsystems, zero third-party licensing risks (zero GPL, zero Apache dependencies), zero real sensitive production data, and complete full-stack capabilities.

---

## 📋 Table of Contents
- [Architecture Overview](#-architecture-overview)
- [Dependencies](#-dependencies)
- [Installation](#-installation)
- [Build](#-build)
- [Run](#-run)
- [Configuration](#-configuration)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Usage & Demo Walkthrough](#-usage--demo-walkthrough)
- [Docker Deployment](#-docker-deployment)
- [License & Governance](#-license--governance)

---

## 🌟 Architecture Overview

The platform is structured into clean enterprise domain layers:

1. **Core Infrastructure & Custom HTTP Engine** (`core/http/`):
   - Multi-threaded native HTTP socket server with keep-alive connection pooling.
   - Dynamic parameter-matching router (`/api/accounts/:id`, `/api/opportunities/:id/stage`).
   - Middleware Pipeline: CORS, Rate Limiting, Request ID tracing, Security Headers, and Static File Streaming.

2. **Fluent Database Engine & Migrations** (`core/database/`):
   - SQL-injection-safe Query Builder supporting `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, `WHERE`, `ORDER BY`, `LIMIT`, and `OFFSET`.
   - Thread-safe SQLite/WAL connection manager with automated schema migrator.

3. **Security, Cryptography & Granular RBAC** (`core/security/`, `config/permissions.py`):
   - Constant-time PBKDF2 password hashing with cryptographically secure random salts.
   - Tamper-evident signed Session/Bearer Tokens with HMAC-SHA256 signatures.
   - Granular RBAC supporting `SUPER_ADMIN`, `SALES_DIRECTOR`, `SALES_REP`, `SUPPORT_LEAD`, `SUPPORT_AGENT`, `MARKETING_MANAGER`, and `AUDITOR`.

4. **Deep Enterprise Domain Sub-Systems** (`modules/`):
   - **Accounts & Customer 360° Profile**: Company hierarchy, annual revenue tracking, and account tiers.
   - **Contacts Directory**: Point-of-contact designation and communication notes.
   - **Inbound Leads & Qualification Engine**: Dynamic lead scoring and 1-Click conversion pipeline.
   - **Sales Pipeline & Interactive Kanban**: 7-stage sales funnel with dynamic win probability adjustment.
   - **Helpdesk & SLA Support Engine**: Priority SLA matrices with real-time breach detection.
   - **Marketing Campaigns & Analytics**: Campaign ROI, CTR, and conversion metrics.
   - **Billing & Recurring Invoicing**: CPQ, multi-currency price books, and dunning engine.
   - **Workflow Automation & Rules**: Event-condition-action pipeline and trigger scheduler.
   - **Custom Reports & BI Aggregator**: Pivot table generator and CSV/JSON/HTML exporters.
   - **Contract Lifecycle & E-Signatures**: Document versioning and digital signature audit ledger.
   - **Territory & Quota Management**: Geographic sales routing and quota attainment tracker.
   - **Predictive Sales Forecasting & Churn AI**: Probability-weighted pipeline and cohort retention analysis.
   - **Customer Portal & Knowledgebase**: Self-service ticketing and search-ranked help center.
   - **Compliance & GDPR Vault**: Opt-in consent registry and right-to-be-forgotten request handler.
   - **Customer Success & Telemetry**: 360-degree health scoring and onboarding milestone pacing.
   - **Team Collaboration & Deal Rooms**: Sales room discussions and asset lockers.

5. **Single-Page Web Dashboard** (`web/`):
   - Zero-dependency modern CSS & Vanilla ES6 JavaScript user interface.

---

## 📦 Dependencies

The platform is designed to be self-contained using the standard runtime, with optional testing utilities:
- **Python**: Version `3.10` or higher (Recommended: Python 3.11 / 3.12)
- **Node.js / npm**: Version `18.0.0` or higher (optional, for package scripts)
- **Docker & Docker Compose**: (optional, for containerized deployments)

All production dependencies are documented in:
- `requirements.txt`
- `pyproject.toml`
- `poetry.lock`
- `package.json`
- `package-lock.json`

---

## 🛠️ Installation

### 1. Clone or Extract the Repository
```bash
git clone <repository_url>
cd CRM
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Alternatively, with npm scripts:
```bash
npm install
```

---

## 🔨 Build

To validate syntax and compile all core and module files:

```bash
# Using Python
python -m py_compile server.py main.py app.py

# Using Makefile
make build

# Using npm
npm run build
```

---

## 🚀 Run

### 1. Quick Launch (Auto-Migrate & Auto-Seed)
```bash
python main.py
```
Or:
```bash
npm start
```
Or:
```bash
make run
```

### 2. Manual Seeding & Server Execution
```bash
# Seed initial mock data
python seeds/mock_crm_data.py

# Start HTTP server
python server.py
```

Once started, open your web browser and navigate to:
```
http://127.0.0.1:8000
```

---

## ⚙️ Configuration

Environment parameters can be supplied via environment variables or configured in `config/app_config.py`.

Available environment variables:
| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `CRM_ENV` | Application environment (`development`, `production`) | `production` |
| `CRM_HOST` | Network interface host to bind server | `127.0.0.1` |
| `CRM_PORT` | HTTP port to listen on | `8000` |
| `CRM_SECRET_KEY` | Cryptographic secret for signing session tokens | `crm-enterprise-key` |
| `CRM_DB_PATH` | SQLite database file storage path | `crm_storage.db` |
| `CRM_RATE_LIMIT` | Max requests per minute per client IP | `600` |

---

## 🧪 Testing & Quality Assurance

To run the full automated test suite covering all 16 domain and integration test specifications:

```bash
# Using Python unittest
python -m unittest discover -s tests -p "test_*.py" -v

# Using Makefile
make test

# Using npm
npm test

# Using pytest (if installed)
pytest tests/ -v
```

---

## 💻 Usage & Demo Walkthrough

### Default Demo Credentials:
- **Super Administrator**: `admin@omnicrm.com` / `Password123!`
- **Sales Director**: `director@omnicrm.com` / `Password123!`
- **Senior Sales Representative**: `rep@omnicrm.com` / `Password123!`
- **Support Lead**: `support@omnicrm.com` / `Password123!`

### Key Functional Flows:
1. **Lead Generation & Scoring**: Add a new inbound lead. The system computes qualification scores from 0-100 based on firmographics and email domain verification.
2. **1-Click Lead Conversion**: Click "Convert Lead" to atomically spawn an Account, a primary Contact, and an Opportunity.
3. **Sales Pipeline & Kanban**: Drag deals across 7 funnel stages. The engine dynamically calculates weighted probabilities and active pipeline values.
4. **Helpdesk & SLAs**: Review incoming tickets. Urgent issues automatically establish 1-hour response and 6-hour resolution countdowns with breach flags.
5. **Executive Analytics**: Real-time KPI cards display total portfolio revenue, lead conversion ratios, customer CSAT scores, and stage-by-stage pipeline velocity.

---

## 🐳 Docker Deployment

### 1. Build and Run with Docker
```bash
docker build -t omniflow-crm:latest .
docker run -d -p 8000:8000 --name omniflow-app omniflow-crm:latest
```

### 2. Deploy with Docker Compose
```bash
docker-compose up --build -d
```
Check logs:
```bash
docker-compose logs -f
```

---

## 📄 License & Governance

Proprietary enterprise software. All rights reserved. This implementation contains 100% original, bespoke code with zero GPL, Apache, or restrictive open-source dependencies.
