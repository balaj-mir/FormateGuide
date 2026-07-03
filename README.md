# 🛡️ FormatGuard — The Turnitin for Academic & Institutional Formatting Compliance

[![Next.js 16](https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19-blue?style=for-the-badge&logo=react&logoColor=white)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com/)

> **FormatGuard** is an enterprise-grade end-to-end web platform engineered to eliminate document formatting non-compliance in academic theses, research dissertations, and corporate reports. It automatically inspects Word documents (`.docx`), verifies compliance against institutional rulesets, generates detailed PDF compliance reports, and produces auto-corrected Word documents with tracked changes.

---

## 📋 Table of Contents
- [Executive Summary](#-executive-summary)
- [Key Features](#-key-features)
- [Technology Stack & Tools](#-technology-stack--tools)
- [System Architecture](#-system-architecture)
- [Document Processing Workflow](#-document-processing-workflow)
- [Project Directory Structure](#-project-directory-structure)
- [Role-Based Access Control (RBAC) Matrix](#-role-based-access-control-rbac-matrix)
- [Local Development & Setup Guide](#-local-development--setup-guide)
  - [Prerequisites](#1-prerequisites)
  - [Environment Variables Setup](#2-environment-variables-setup)
  - [Running with Docker Compose (Recommended)](#3-running-with-docker-compose-recommended)
  - [Running Manually (Without Docker)](#4-running-manually-without-docker)
- [API Reference & Endpoints](#-api-reference--endpoints)
- [Security & Compliance](#-security--compliance)
- [License & Contributing](#-license--contributing)

---

## 🎯 Executive Summary

In universities and research institutions worldwide, formatting verification for theses and project reports is a tedious, manual, and error-prone process. Reviewers spend countless hours checking margins, font sizes, line spacing, heading styles, and citation formats instead of evaluating academic content.

**FormatGuard** solves this by automating the entire compliance pipeline:
1. **Deep XML Inspection**: Parses the underlying XML structure of Microsoft Word (`.docx`) documents to evaluate exact typographic and structural properties.
2. **Institutional Ruleset Matching**: Compares document metrics against standardized schemas (e.g., APA 7th, IEEE, Harvard, NUST, COMSATS, HEC Pakistan).
3. **Automated Remediation**: Directly modifies XML formatting tags (`w:rPr`, `w:pPr`) without altering user text, generating a clean, tracked-changes `.docx` ready for submission.

---

## ✨ Key Features

* **🔬 Precision XML Document Parsing**: Extracts and validates font families, font sizes, margins, line spacing, paragraph indents, text alignment, heading hierarchies (H1–H6), and Table of Contents (TOC) structures.
* **🏛️ Pre-Built Institutional Rulesets**: Ships with pre-configured JSON schemas for major academic institutions and publishing standards:
  * *APA 7th Edition*
  * *IEEE Citation & Format Standard*
  * *Harvard Formatting Guidelines*
  * *HEC Pakistan Thesis Guidelines*
  * *NUST, COMSATS, & FAST-NUCES Standards*
* **🛠️ Tracked-Changes Auto-Correction Engine**: Automatically generates a corrected `.docx` file highlighting every formatting adjustment made by the engine for transparent review.
* **📊 Professional PDF Compliance Reports**: Generates downloadable, audit-ready PDF compliance certificates using **ReportLab** with section-by-section breakdown of formatting errors.
* **🔐 Multi-Tier RBAC & Subscription Quotas**: Supports Free and Premium user tiers with role-based permissions for Students, Faculty Reviewers, and Institutional Admins.
* **⚡ Asynchronous Background Processing**: Offloads heavy XML parsing and report generation to a high-performance **Celery** distributed task queue backed by **Redis**.

---

## 🛠️ Technology Stack & Tools

### **Frontend Architecture**
| Component | Technology / Library | Description |
| :--- | :--- | :--- |
| **Framework** | Next.js 16 (App Router) | Modern server-side rendered React framework with optimized routing. |
| **UI Library** | React 19 & TypeScript | Strongly-typed component architecture for robust front-end logic. |
| **Styling** | Tailwind CSS v4 & Framer Motion | Utility-first styling with smooth micro-animations and responsive layouts. |
| **State Management** | Zustand | Lightweight, hook-based global state management. |
| **Icons & UI Components** | Lucide React & Radix UI | Clean, accessible icon sets and headless UI primitives. |

### **Backend Architecture**
| Component | Technology / Library | Description |
| :--- | :--- | :--- |
| **API Framework** | FastAPI (Python 3.12) | High-performance asynchronous REST API with automatic OpenAPI docs. |
| **ORM & Database** | Async SQLAlchemy 2.0 & PostgreSQL | Non-blocking database operations connected to Supabase PostgreSQL. |
| **Validation & Serialization** | Pydantic v2 | High-speed schema validation and type checking. |
| **Migrations** | Alembic | Version-controlled database schema migrations. |
| **Background Queue** | Celery & Redis | Distributed worker queue for heavy document processing jobs. |
| **Monitoring** | Flower & Structlog | Real-time Celery task dashboard and JSON structured logging. |

### **Document Processing & Cloud Infrastructure**
| Component | Technology / Library | Description |
| :--- | :--- | :--- |
| **DOCX Parsing & XML** | `python-docx` & `lxml` | Direct manipulation of Word OpenXML document structures. |
| **PDF Generation** | ReportLab | Programmatic generation of high-resolution compliance PDFs. |
| **Authentication** | Supabase Auth (JWT Bearer) | Secure stateless token verification and user identity management. |
| **File Storage** | AWS S3 / Cloudflare R2 | Scalable object storage with time-limited pre-signed URLs. |
| **Containerization** | Docker & Docker Compose | Multi-container Docker setup for reproducible deployments. |

---

## 🏗️ System Architecture

The following diagram illustrates the high-level system architecture and data flow between client applications, backend services, workers, and cloud providers:

```mermaid
graph TD
    subgraph Client Layer
        UI[Next.js 16 Frontend<br/>Tailwind CSS / React 19]
    end

    subgraph API & Gateway Layer
        API[FastAPI Backend Server<br/>Port 8000]
        AUTH[Supabase Auth JWT]
    end

    subgraph Asynchronous Processing Layer
        REDIS[(Redis Broker<br/>Port 6379)]
        WORKER[Celery Task Worker<br/>XML Parser & Auto-Corrector]
        FLOWER[Flower Dashboard<br/>Port 5555]
    end

    subgraph Data & Storage Layer
        DB[(PostgreSQL Database<br/>Supabase ORM)]
        S3[(Cloudflare R2 / AWS S3<br/>Document Storage)]
    end

    UI -->|HTTPS REST / JWT| API
    UI -->|Auth Requests| AUTH
    API -->|Validate JWT| AUTH
    API -->|Read / Write Metadata| DB
    API -->|Upload Original DOCX| S3
    API -->|Dispatch Job Task| REDIS
    REDIS -->|Consume Task| WORKER
    WORKER -->|Monitor Stats| FLOWER
    WORKER -->|Download DOCX| S3
    WORKER -->|Parse XML & Correct| WORKER
    WORKER -->|Upload Corrected DOCX & PDF| S3
    WORKER -->|Update Status & Score| DB
```

---

## 🔄 Document Processing Workflow

When a user submits a thesis or report for compliance verification, the platform executes the following automated pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor User as Student / Faculty
    participant FE as Next.js Frontend
    participant BE as FastAPI Backend
    participant S3 as AWS S3 / Cloudflare R2
    participant Q as Redis Queue
    participant W as Celery Worker
    participant DB as PostgreSQL DB

    User->>FE: Select DOCX & Institutional Ruleset
    FE->>BE: POST /api/submissions (File + Ruleset ID)
    BE->>S3: Upload Original DOCX File
    S3-->>BE: Return File UUID URL
    BE->>DB: Create Submission Record (Status: PENDING)
    BE->>Q: Push Processing Task (submission_id)
    BE-->>FE: Return Submission ID & PENDING status
    FE->>BE: Poll /api/submissions/{id} for status updates

    Q->>W: Dequeue Processing Task
    W->>DB: Update Status -> PROCESSING
    W->>S3: Download Original DOCX File
    W->>W: Deep XML Parsing (python-docx / lxml)
    W->>W: Evaluate against Ruleset JSON Schema
    W->>W: Generate ReportLab Compliance PDF
    W->>W: Apply XML Corrections (Tracked Changes DOCX)
    W->>S3: Upload Corrected DOCX & Report PDF
    W->>DB: Update Status -> COMPLETED (Store Score & URLs)
    
    FE->>BE: Poll receives Status: COMPLETED
    FE-->>User: Display Compliance Score, Error Breakdown & Download Links
```

---

## 📂 Project Directory Structure

```text
FormatGuard/
├── docker-compose.yml              # Multi-container Docker orchestration
├── README.md                       # Comprehensive project documentation
├── .gitignore                      # Git exclusion rules
│
├── backend/                        # FastAPI Backend Application
│   ├── Dockerfile                  # Backend container configuration
│   ├── requirements.txt            # Python dependencies
│   ├── alembic.ini                 # Alembic migration configuration
│   ├── alembic/                    # Database migration versions
│   └── app/
│       ├── main.py                 # FastAPI app entry point & middleware setup
│       ├── config.py               # Environment settings & Pydantic config
│       ├── database.py             # Async SQLAlchemy session factory
│       ├── dependencies.py         # JWT Auth & database dependencies
│       ├── core/                   # Exception handlers & structured logging
│       ├── models/                 # SQLAlchemy database models
│       ├── schemas/                # Pydantic request/response schemas
│       ├── routers/                # REST API route controllers
│       │   ├── auth.py             # User authentication endpoints
│       │   ├── submissions.py      # Document upload & tracking endpoints
│       │   ├── rulesets.py         # Institutional ruleset management
│       │   ├── reports.py          # Compliance report generation API
│       │   ├── corrections.py      # Auto-correction download API
│       │   └── admin.py            # Administrative analytics & user management
│       ├── services/               # Core business logic & XML processing
│       │   ├── parser_service.py   # DOCX XML extractor & font/margin analyzer
│       │   ├── ruleset_service.py  # Institutional ruleset evaluator
│       │   ├── correction_engine.py# XML tag modifier for auto-correction
│       │   ├── report_service.py   # ReportLab PDF report builder
│       │   └── storage_service.py  # AWS S3 / Cloudflare R2 cloud storage
│       └── tasks/                  # Celery background worker tasks
│
└── frontend/                       # Next.js 16 Frontend Application
    ├── package.json                # Node.js dependencies & scripts
    ├── tsconfig.json               # TypeScript configuration
    ├── next.config.ts              # Next.js optimization & environment settings
    ├── tailwind.config.ts / css    # Tailwind CSS v4 design tokens & styles
    ├── public/                     # Static assets & logos
    └── app/                        # Next.js App Router pages
        ├── layout.tsx              # Global application layout & providers
        ├── page.tsx                # Landing page & hero section
        ├── (auth)/                 # Authentication pages (Login / Register)
        └── dashboard/              # Protected User & Admin Dashboard
            ├── page.tsx            # Dashboard overview & recent submissions
            ├── upload/             # Document drag-and-drop upload interface
            ├── submissions/        # Submission history & compliance viewer
            ├── rulesets/           # Institutional ruleset explorer
            ├── reports/            # PDF report download center
            └── admin/              # Admin control panel & user management
```

---

## 👥 Role-Based Access Control (RBAC) Matrix

FormatGuard implements granular permission controls to support institutional workflows:

| Feature / Capability | 🟢 Free Student | 🔵 Premium Student | 🟣 Faculty Reviewer | 🔴 Institutional Admin |
| :--- | :center: | :center: | :center: | :center: |
| **Monthly Document Uploads** | 5 docs / month | Unlimited | Unlimited | Unlimited |
| **Standard Ruleset Verification** | ✔️ Yes | ✔️ Yes | ✔️ Yes | ✔️ Yes |
| **PDF Compliance Report Download** | ✔️ Basic Summary | ✔️ Full Detail PDF | ✔️ Full Detail PDF | ✔️ Full Detail PDF |
| **Tracked-Changes Auto-Correction** | ❌ No | ✔️ Yes | ✔️ Yes | ✔️ Yes |
| **Batch Document Review** | ❌ No | ❌ No | ✔️ Yes | ✔️ Yes |
| **Create / Modify Institutional Rulesets**| ❌ No | ❌ No | ❌ No | ✔️ Yes |
| **Manage Users & System Analytics** | ❌ No | ❌ No | ❌ No | ✔️ Yes |

---

## 💻 Local Development & Setup Guide

### 1. Prerequisites
Ensure you have the following software installed on your system:
* **Docker & Docker Compose** (v2.20+ recommended)
* **Node.js** (v18+ or v20 LTS) & **npm**
* **Python** (v3.12+ if running backend without Docker)
* **Git**

### 2. Environment Variables Setup
Create `.env` files in both the `backend/` and `frontend/` directories by copying from their respective examples:

#### **Backend Configuration (`backend/.env`)**
```env
# Database & Broker
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db.your-project.supabase.co:5432/postgres
REDIS_URL=redis://localhost:6379/0

# Supabase Authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your_supabase_jwt_secret

# Cloud Storage (AWS S3 or Cloudflare R2)
AWS_ACCESS_KEY_ID=your_s3_access_key
AWS_SECRET_ACCESS_KEY=your_s3_secret_key
S3_BUCKET_NAME=formatguard-docs
S3_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com

# AI & Optional Integrations
OPENAI_API_KEY=sk-your-openai-api-key
SENTRY_DSN=
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### **Frontend Configuration (`frontend/.env.local`)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

### 3. Running with Docker Compose (Recommended)
The fastest way to launch the complete backend stack (FastAPI, Celery Worker, Redis Broker, and Flower Dashboard) is via Docker Compose:

1. **Open a terminal in the project root directory**:
   ```bash
   cd FormateGuide/formatguard
   ```

2. **Launch the backend containers**:
   ```bash
   docker-compose up --build -d
   ```
   *This initializes the following services:*
   * 🌐 **FastAPI Backend Server**: `http://localhost:8000` (API Docs at `/api/docs`)
   * ⚙️ **Celery Worker**: Background task executor
   * ⚡ **Redis Broker**: `localhost:6379`
   * 🌸 **Flower Monitoring Dashboard**: `http://localhost:5555`

3. **Run Database Migrations**:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

4. **Start the Next.js Frontend Development Server**:
   In a new terminal window:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *Access the web application at **`http://localhost:3000`**.*

---

### 4. Running Manually (Without Docker)
If you prefer running services natively on your host machine:

1. **Start a Local Redis Server**: Ensure Redis is running on port `6379`.
2. **Setup Backend Python Virtual Environment**:
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   
   pip install -r requirements.txt
   alembic upgrade head
   ```
3. **Launch FastAPI Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. **Launch Celery Worker** (in a separate terminal inside `backend/`):
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info -P solo
   ```
   *(Note: `-P solo` or `-P gevent` is recommended on Windows hosts).*

---

## 📡 API Reference & Endpoints

When the backend server is running, interactive OpenAPI documentation is automatically available at **`http://localhost:8000/api/docs`**.

### **Core Endpoints Overview**
* `POST /api/auth/register` — Register a new student or faculty account.
* `POST /api/auth/login` — Authenticate and obtain JWT Bearer access token.
* `GET /api/rulesets` — List all available institutional formatting rulesets.
* `POST /api/submissions` — Upload a `.docx` file for automated compliance analysis.
* `GET /api/submissions/{id}` — Check status, compliance score, and error breakdown.
* `GET /api/reports/{submission_id}/download` — Generate and download ReportLab PDF audit report.
* `GET /api/corrections/{submission_id}/download` — Download tracked-changes auto-corrected Word document.
* `GET /api/admin/analytics` — Retrieve institutional usage metrics and compliance statistics (Admin only).

---

## 🔒 Security & Compliance

FormatGuard adheres to strict academic integrity and data privacy standards:
* **Zero Textual Alteration Guarantee**: The auto-correction engine strictly modifies XML presentation attributes (`w:rPr`, `w:pPr`, margins, line spacing) and **never** alters, deletes, or modifies user text, citations, or data.
* **Transient Cloud Storage**: Uploaded documents are stored using cryptographically secure UUIDs in private S3/R2 buckets. Access is restricted exclusively via time-limited, pre-signed URLs.
* **Stateless Authentication**: All API requests are verified using signed JWT Bearer tokens issued by Supabase Auth with strict CORS policy enforcement.

---

## 📄 License & Contributing

This project is developed for institutional academic compliance evaluation. Contributions, bug reports, and institutional schema suggestions are welcome! Please open an issue or pull request on GitHub.

**Repository**: [https://github.com/balaj-mir/FormateGuide](https://github.com/balaj-mir/FormateGuide)
