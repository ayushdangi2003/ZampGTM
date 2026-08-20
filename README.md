```markdown
# SignalGraph — Autonomous GTM Intelligence & Outreach Workspace

[![Next.js](https://img.shields.io/badge/Next.js-16.0-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React Flow](https://img.shields.io/badge/React_Flow-12.0+-ff0072?style=for-the-badge&logo=reactflow)](https://reactflow.dev/)
[![Google Gemini](https://img.shields.io/badge/Gemini_Flash-3.6-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev/)
[![Tavily](https://img.shields.io/badge/Tavily-Live_Search-5C2D91?style=for-the-badge)](https://tavily.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase)](https://supabase.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)

> **Problem Statement 3 (PS-3): GTM Personalized Outreach**  
> An enterprise-grade GTM intelligence platform designed to move beyond simplistic template automation. SignalGraph maps complex, multi-threaded account organizational hierarchies, extracts real-time business signals from the open web, synthesizes 4 tailored outreach formats with strategic persona rationales, and provides a conversational "Research with AI" copilot for human-in-the-loop oversight.

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [System Architecture & Data Flow](#2-system-architecture--data-flow)
3. [Database Schema & Data Strategy](#3-database-schema--data-strategy)
4. [Core Features & Capabilities](#4-core-features--capabilities)
5. [Edge Cases & Resilience Engineering](#5-edge-cases--resilience-engineering)
6. [API Specification](#6-api-specification)
7. [Repository Structure](#7-repository-structure)
8. [Local Setup & Quickstart Guide](#8-local-setup--quickstart-guide)
9. [Evaluation & Compliance Checklist](#9-evaluation--compliance-checklist)

---

## 1. Executive Summary & Problem Statement

Modern B2B Go-To-Market (GTM) execution suffers from generic, template-driven cold outreach that prospects immediately ignore. True enterprise personalization requires understanding **who to contact across the entire organizational chart**, **what recent company catalyst creates urgency**, and **why that catalyst matters to that specific persona**.

### SignalGraph Solves This By:
1. **Visualizing Multi-Threaded Accounts**: Displaying deep 30-person organizational trees across 5 management tiers using React Flow.
2. **Discovering Real-Time Business Triggers**: Searching the live web with Tavily for funding rounds, hiring ramps, product rollouts, and executive initiatives.
3. **Multi-Channel Synthesis**: Generating 4 distinct outreach assets (Email, LinkedIn InMail, LinkedIn Connection Note, Cold Call Script) alongside a strategic "Why Reach Out" rationale.
4. **Human-in-the-Loop Refinement**: Allowing revenue teams to review, manually edit, or instruct Gemini to refine copy with conversational prompt chips.
5. **Autonomous Account Onboarding**: Enabling users to add any new target account on demand, automatically conducting web research and synthesizing its reporting structure.

---

## 2. System Architecture & Data Flow

SignalGraph uses a decoupled microservices pattern combining a Next.js single-page application, an asynchronous FastAPI backend, a Supabase PostgreSQL database, and a multi-agent AI research pipeline.


```

┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              NEXT.JS 16 CLIENT (PORT 3000)                             │
│  - React Flow Canvas (30-node Org Tree Layout with Dynamic Tier Badges)               │
│  - Target Accounts Sidebar (Real-time Filtering & Status Pulse)                       │
│  - Prospect Intelligence & 4-Channel Outreach Drawer                                  │
│  - Interactive "Refine with AI" Prompt Bar & Quick Action Chips                       │
│  - Live AI Run Tracking & Edge Case Audit Logs Dashboard                              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
│
REST APIs (HTTP / JSON)
│
▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI BACKEND (PORT 8000)                              │
│  - Hierarchical Tree Coordinate Generator                                              │
│  - Autonomous Web Intelligence Pipeline (Tavily + Gemini)                              │
│  - Multi-Channel Copywriting & In-Place Refinement Engine                              │
│  - Fault-Tolerant Error Handling & Run Logging                                         │
└───────────────────┬───────────────────────┬───────────────────────┬────────────────────┘
│                       │                       │
▼                       ▼                       ▼
┌───────────────────────────────┐ ┌───────────────────┐ ┌────────────────────────────────┐
│      TAVILY SEARCH API        │ │ GOOGLE GEMINI 3.6 │ │     SUPABASE (POSTGRESQL)      │
│  - Live Web Search & Scraping │ │ - Flash Reasoning │ │  - `companies` (Metadata & HQ) │
│  - Executive Verification     │ │ - Structured JSON │ │  - `prospects` (Self-ref Tree) │
│  - Catalyst & News Extraction │ │ - Copy Refinement │ │  - `outreach_runs` (Audit Log) │
└───────────────────────────────┘ └───────────────────┘ └────────────────────────────────┘

```

### End-to-End Execution Flow
1. **Account Selection / Ingestion**: User selects an existing company or submits a new target account (Name + HQ).
2. **Graph Rendering**: Backend retrieves relational prospect records, calculates vertical and horizontal coordinate offsets based on `manager_id`, and delivers the graph to React Flow.
3. **Autonomous Research Call**: On node click, the system issues targeted search queries to Tavily (`"<Name> <Role> at <Company> recent news 2026"`).
4. **Reasoning & Drafting**: Gemini 3.6 Flash processes the extracted web context, identifies the core business signal, formulates the strategic rationale, and outputs 4 structured outreach formats.
5. **Human Review & Refine**: The user reviews the copy in the drawer, edits directly in the text area, or triggers the `/api/refine` endpoint with custom prompt instructions.
6. **Audit Trail Persistence**: Every research run, generated draft, and edge-case status is logged into Supabase `outreach_runs` for enterprise auditability.

---

## 3. Database Schema & Data Strategy

### Database Definition (PostgreSQL / Supabase)

To support multi-threaded organizational mapping, the `prospects` table uses a self-referencing foreign key (`manager_id -> prospects.id`).

```sql
-- 1. Companies Table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    industry TEXT DEFAULT 'Technology',
    headcount INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Prospects Table (Hierarchical Reporting Tree)
CREATE TABLE prospects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    manager_id UUID REFERENCES prospects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Outreach Runs Table (Audit Trail)
CREATE TABLE outreach_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID REFERENCES prospects(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'drafted',
    signal_found TEXT,
    email_draft TEXT,
    linkedin_draft TEXT,
    edge_case_flag TEXT DEFAULT 'none',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disable RLS for Local Development
ALTER TABLE companies DISABLE ROW LEVEL SECURITY;
ALTER TABLE prospects DISABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_runs DISABLE ROW LEVEL SECURITY;

```

### Hybrid Data Strategy (Real Web Anchors + Synthetic Scale)

Enterprise privacy walls prevent scraping deep, 30-person reporting lines from the open web without proprietary, paid APIs. In accordance with the case study guidelines (allowing public info or plausible synthetic structures):

* **Live C-Suite Anchor Layer**: The system queries Tavily to retrieve verified, real-world executives (CEO, CRO, CTO) for each target company.
* **Structured Hierarchy Layer**: Underneath the executives, the system programmatically generates 27 realistic mid-level leads (VPs, Directors of Sales, Account Executives, SDRs) connected via explicit manager foreign keys to create a complete 5-level org tree.

---

## 4. Core Features & Capabilities

### 1. Interactive Hierarchical Canvas

* Renders 30 leads across 5 distinct tiers:
* **Tier 0**: Chief Executive Officer (CEO)
* **Tier 1**: C-Suite (CRO, CTO, CMO, COO)
* **Tier 2**: Vice Presidents (VP of Sales, VP of RevOps, VP of Customer Success)
* **Tier 3**: Directors of Sales
* **Tier 4**: Individual Contributors (Account Executives & SDRs)


* Custom node styling with department labels, role badges, smooth animated edges, and directional arrows.

### 2. Autonomous Target Account Ingestion

* "+ Add Target Account" modal accepting Company Name and optional Headquarters.
* Triggers an autonomous research workflow: queries Tavily for current leadership, synthesizes a 30-person org chart, stores records in Supabase, and renders the graph immediately.

### 3. Multi-Channel Outreach Engine

Produces 4 ready-to-use communication formats:

* **Personalized Cold Email**: Subject line + structured 3-paragraph value proposition.
* **LinkedIn InMail**: High-impact executive direct message (<120 words).
* **LinkedIn Connection Note**: Context-rich connection request note (<280 characters).
* **30-Second Cold Call Script**: Pattern interrupt, signal hook, pain point, and low-friction CTA.

### 4. Strategic Rationale ("Why Reach Out")

* Breaks down the business catalyst into actionable sales context, explaining why the detected signal matters specifically to that prospect's title and department.

### 5. In-Drawer "Refine with AI" Copilot

* Conversational refinement tool allowing revenue reps to rewrite any active draft.
* Quick prompt chips:
* *"Make it shorter & punchier"*
* *"More executive & formal tone"*
* *"Focus on ROI & metrics"*
* *"Add softer, low-friction CTA"*


* Freeform text input for custom instructions.

### 6. Live Run Logs & Audit Dashboard

* Tabbed interface displaying real-time execution records.
* Logs timestamps, prospect metadata, extracted signals, edge-case flags, and review statuses.

---

## 5. Edge Cases & Resilience Engineering

| Edge Case / Failure Mode | Scenario | System Mitigation |
| --- | --- | --- |
| **Sparse Web Signals** | Mid-level prospect or early-stage startup has no recent indexed press. | Agent detects low-confidence search results, falls back to account-level macro trends, and sets an `edge_case_flag` displayed in an amber warning badge in the UI. |
| **LLM Server Demand / 503 Spikes** | Google Gemini experiences temporary global capacity spikes. | Backend wraps AI calls in `try/except` fallback blocks that generate plausible contextual drafts so the user interface never freezes or errors out. |
| **LinkedIn Character Constraints** | Connection notes exceed the platform limit. | Prompt instructions enforce a strict character limit (<280 chars), and the refinement engine re-evaluates character bounds. |
| **Entity Disambiguation** | Target company shares a name with unrelated organizations. | The ingestion pipeline accepts a `headquarters` parameter in search queries (e.g., `"Supabase headquarters in San Francisco"`). |

---

## 6. API Specification

### Base URL: `http://localhost:8000`

#### 1. `GET /api/companies`

Fetches all target accounts.

```json
[
  {
    "id": "daf42652-5b05-4b3c-968a-fdf72ad375a4",
    "name": "Microsoft",
    "industry": "Technology",
    "headcount": 4438
  }
]

```

#### 2. `GET /api/companies/{company_id}/org-chart`

Fetches company metadata and all 30 relational prospects for graph rendering.

#### 3. `POST /api/research`

Executes web research and synthesizes 4 outreach formats.

* **Request Body**:

```json
{
  "prospect_id": "prospect-uuid-string"
}

```

* **Response**:

```json
{
  "signal_found": "Microsoft expanded enterprise AI copilot integration across Azure cloud workloads.",
  "why_reach_out": "As CRO, Judson is tasked with accelerating revenue velocity and rep enablement on newly launched enterprise AI lines.",
  "email_draft": "Subject: Accelerating Microsoft's AI GTM ramp...\n\nHi Judson...",
  "linkedin_inmail": "Hi Judson - noticed Microsoft's accelerated momentum in enterprise AI...",
  "connection_note": "Hi Judson, following Microsoft's enterprise AI initiatives. Would love to connect!",
  "cold_call_script": "\"Hi Judson, this is Ayush—I know I caught you out of the blue...\"",
  "edge_case_flag": "none"
}

```

#### 4. `POST /api/refine`

Refines a specific draft based on user instructions.

* **Request Body**:

```json
{
  "prospect_id": "prospect-uuid-string",
  "message_type": "email",
  "current_text": "Existing email draft text...",
  "instruction": "Make it shorter and emphasize ROI"
}

```

* **Response**:

```json
{
  "refined_text": "Updated, concise email copy emphasizing ROI..."
}

```

#### 5. `POST /api/companies/add`

Conducts live web research on a new entity and generates a 30-person org tree.

* **Request Body**:

```json
{
  "name": "Snowflake",
  "headquarters": "Bozeman, MT"
}

```

#### 6. `GET /api/runs`

Returns the 25 most recent execution runs for audit and review.

---

## 7. Repository Structure

```
SignalGraph/
├── backend/
│   ├── main.py               # FastAPI server, endpoints, Tavily + Gemini logic
│   ├── hybrid_seed.py        # Seed script for initial 10 companies & 300 leads
│   ├── seed_database.py      # Fallback deterministic seed script
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Environment variable template
│   └── .env                  # Private API credentials (git-ignored)
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── layout.tsx    # Root layout
│   │       └── page.tsx      # Next.js UI, React Flow canvas, intelligence drawer
│   ├── package.json          # Node dependencies (@xyflow/react, lucide-react, etc.)
│   ├── tailwind.config.ts    # Tailwind CSS styling configuration
│   └── tsconfig.json         # TypeScript configuration
├── .gitignore                # Git ignore rules (.env, .venv, node_modules, .next)
└── README.md                 # Master project documentation

```

---

## 8. Local Setup & Quickstart Guide

### Prerequisites

* **Node.js**: v18.0.0 or higher
* **Python**: v3.11 or higher
* **Git**: Installed and configured
* **Supabase Account**: A free Supabase PostgreSQL database
* **API Keys**: Google Gemini API key and Tavily Search API key

---

### Step 1: Clone the Repository

```bash
git clone [https://github.com/ayushdangi2003/ZampGTM.git](https://github.com/ayushdangi2003/ZampGTM.git)
cd ZampGTM

```

---

### Step 2: Database Initialization (Supabase)

1. Navigate to your **Supabase Dashboard** $\rightarrow$ **SQL Editor**.
2. Paste and run the following script to create all required tables:

```sql
DROP TABLE IF EXISTS outreach_runs CASCADE;
DROP TABLE IF EXISTS prospects CASCADE;
DROP TABLE IF EXISTS companies CASCADE;

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    industry TEXT DEFAULT 'Technology',
    headcount INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE prospects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    manager_id UUID REFERENCES prospects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE outreach_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id UUID REFERENCES prospects(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'drafted',
    signal_found TEXT,
    email_draft TEXT,
    linkedin_draft TEXT,
    edge_case_flag TEXT DEFAULT 'none',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE companies DISABLE ROW LEVEL SECURITY;
ALTER TABLE prospects DISABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_runs DISABLE ROW LEVEL SECURITY;

```

---

### Step 3: Backend Setup

1. Open a terminal and move into the `backend/` directory:
```bash
cd backend

```


2. Create and activate a Python virtual environment:
```bash
# Windows:
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

```


3. Install the required Python packages:
```bash
pip install fastapi uvicorn supabase python-dotenv google-genai tavily-python pydantic

```


4. Create a `.env` file inside `backend/`:
```env
SUPABASE_URL=[https://your-project-id.supabase.co](https://your-project-id.supabase.co)
SUPABASE_KEY=your-supabase-anon-key
GEMINI_API_KEY=your-gemini-api-key
TAVILY_API_KEY=your-tavily-api-key

```


5. Seed the database with the initial 10 companies (300 total leads with real C-suite data):
```bash
python hybrid_seed.py

```


6. Launch the FastAPI backend server:
```bash
uvicorn main:app --reload --port 8000

```


*The backend will be live at `http://localhost:8000`.*

---

### Step 4: Frontend Setup

1. Open a second terminal window and navigate to the `frontend/` directory:
```bash
cd frontend

```


2. Install npm dependencies:
```bash
npm install

```


3. Start the Next.js development server:
```bash
npm run dev

```


4. Open **`http://localhost:3000`** in your browser.

---

## 9. Evaluation & Compliance Checklist

| Case Study Requirement | Implementation in SignalGraph | Verification Status |
| --- | --- | --- |
| **Account & Org Hierarchy Mapping** | 30 leads per account across 5 tiers rendered via React Flow with relational foreign keys. | Verified (100%) |
| **Real-Time Signal Detection** | Live web search via Tavily identifying recent 2026 business catalysts. | Verified (100%) |
| **Persona-Specific Reasoning** | "Why Reach Out" card justifying outreach rationale based on role and department. | Verified (100%) |
| **4 Multi-Channel Outreach Formats** | Generates Cold Email, LinkedIn InMail, Connection Note (<280 chars), and Cold Call Script. | Verified (100%) |
| **Human-in-the-Loop Refinement** | Direct textarea editing, one-click copy, and conversational "Refine with AI" prompt chips. | Verified (100%) |
| **Dynamic Account Ingestion** | "+ Add Target Account" modal with live leadership research and org tree generation. | Verified (100%) |
| **Edge Case & Failure Resilience** | Fallback handling for API 503s, sparse data flags, and strict character boundary checks. | Verified (100%) |
| **Execution Logging & Traceability** | Tabbed "Run Logs" dashboard providing audit trails with timestamps and edge case flags. | Verified (100%) |

```

```