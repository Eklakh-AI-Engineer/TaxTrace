# TaxTrace Pilot Onboarding Guide

**Version:** 1.0  
**Date:** 2026-10-04  
**Audience:** Pilot CA firms, implementation team

---

## 1. Overview

This guide walks you through setting up and running a TaxTrace pilot for your CA firm. The pilot validates the core reconciliation workflow:

**Upload Purchase Register → Upload GSTR-2B → Reconcile → Review Exceptions → Export Report**

---

## 2. Prerequisites

### System Requirements
- Modern web browser (Chrome, Firefox, Edge)
- Internet connection for API access
- Sample data files (provided below)

### Sample Data
Download the pilot dataset:
- `evaluations/datasets/pilot_books.csv` — Purchase Register (200 transactions)
- `evaluations/datasets/pilot_gstr2b.csv` — GSTR-2B (181 transactions)
- `evaluations/datasets/ground_truth.json` — Expected results for validation

---

## 3. Quick Start (5 minutes)

### Option A: Using Docker (Recommended)
```bash
# Clone and start
git clone <repo-url>
cd TaxTrace
docker-compose up -d

# Access frontend
open http://localhost:3000

# API available at
http://localhost:8000/docs
```

### Option B: Local Development
```bash
# Backend
cd backend
.venv/Scripts/activate  # Windows
pip install -e .
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
# Access at http://localhost:3000
```

---

## 4. Pilot Workflow Walkthrough

### Step 1: Login
Use development token:
```
Authorization: Bearer dev.user-1.firm-1.senior
```
Or use the web UI with pre-configured demo credentials.

### Step 2: Create Client & Period
1. Navigate to **Clients** → **Create Client**
   - Name: "Pilot Client Ltd"
   - GSTIN: "27AAACT2727Q1ZW"
2. Navigate to **Periods** → **Create Period**
   - Financial Year: "2026-27"
   - Tax Period: "M1" (April 2026)
   - Link to Pilot Client

### Step 3: Upload Purchase Register
1. Go to **Documents** → **Upload**
2. Select `pilot_books.csv`
3. Document Type: "purchase_register"
4. Select the Client and Period created above
4. Click **Upload**
5. Verify: 200 transactions extracted ✓

### Step 4: Upload GSTR-2B
1. Go to **Documents** → **Upload**
2. Select `pilot_gstr2b.csv`
3. Document Type: "gstr2b"
4. Same Client and Period
5. Click **Upload**
6. Verify: 181 transactions extracted ✓

### Step 5: Run Reconciliation
1. Go to **Reconciliation** → **Run**
2. Select Client and Period
3. Click **Run Reconciliation**
3. Wait for completion (typically < 5 seconds)
4. Review Summary:
   - Matched: ~159
   - Value Mismatch: ~22
   - Missing in 2B: ~19
   - (Matches ground truth benchmarks)

### Step 6: Review Exceptions
1. Go to **Exceptions** page
2. Filter by severity: "High"
3. Click on a **VALUE_MISMATCH** exception
4. Review:
   - Side-by-side book vs portal values
   - Evidence panel with source rows
   - AI Explanation (click "Explain")
5. Make Decision: **Accept** / **Reject** / **Needs Info**
6. Add comment if needed

### Step 7: Export Report
1. On Exceptions page, click **Export CSV**
2. Download `reconciliation-report-<period-id>-<date>.csv`
3. Open in Excel/CSV viewer
4. Verify columns:
   - Exception ID, Type, Severity, Status
   - Book Invoice, Portal Invoice
   - Book/Portal Taxable, CGST, SGST, IGST
   - Match Score, Evidence References

---

## 5. Notice Workflow (Optional)

### Upload Notice
1. Go to **Notices** → **Upload**
2. Upload a DRC-01 or ASMT-10 PDF
3. Select Client and Period

### Extract Facts
1. Click **Extract Facts** on the notice
2. Review extracted:
   - Notice type (DRC-01, ASMT-10, etc.)
   - Reference number, dates, demand amount
   - Cited sections

### Generate Draft
1. Click **Generate Draft**
2. Enter instructions: "Draft preliminary reply denying demand"
3. Review draft with:
   - Cited sections highlighted
   - Missing information flags
   - Editable content

### Approve (Partner Only)
1. Partner login required
2. Click **Approve for Use**
3. Add approval comment
4. Draft status → "Approved"

---

## 6. Expected Benchmark Results

| Metric | Target | Pilot Dataset |
|--------|--------|---------------|
| Matched Precision | ≥ 90% | 100% |
| Matched Recall | ≥ 85% | 100% |
| Missing in 2B Precision | ≥ 90% | 100% |
| Missing in 2B Recall | ≥ 85% | 100% |
| Value Mismatch Precision | ≥ 90% | 100% |
| Value Mismatch Recall | ≥ 85% | 100% |

Run benchmark:
```bash
.venv/Scripts/python.exe evaluations/benchmark_reconciliation.py
```

---

## 7. WhatsApp Simulator

Test bot commands without Meta credentials:
1. Go to **Chat Simulator** page
2. Try commands:
   - `help` — Show menu
   - `show pending tasks` — List open tasks
   - `review tasks` — Task summary
   - `show deadlines` — Upcoming notice deadlines
   - `explain mismatch <exception-id>` — AI explanation

---

## 8. Feedback Collection

After completing the pilot, please provide feedback on:

| Area | Rating (1-5) | Comments |
|------|-------------|----------|
| Upload & parsing reliability | | |
| Reconciliation accuracy | | |
| Exception review UX | | |
| AI explanation quality | | |
| Notice workflow | | |
| Export report usefulness | | |
| Overall time savings | | |
| Bugs / issues encountered | | |

**Time tracking:**
- Manual reconciliation time (before): ___ minutes
- TaxTrace reconciliation time (after): ___ minutes
- Time saved: ___%

---

## 9. Known Limitations (Pilot)

| Limitation | Workaround |
|------------|------------|
| CSV/XLSX only (no PDF OCR) | Use provided CSV files |
| Single-period view | Select period from dropdown |
| Mock AI provider only | Explanations are template-based |
| No Tally/Busy direct import | Export to CSV first |
| Single-tenant demo | Data isolated per firm |

---

## 10. Support & Escalation

| Issue | Contact |
|-------|---------|
| Technical bugs | Create GitHub issue |
| Data/questions | pilot-support@taxtrace.example |
| Security concerns | security@taxtrace.example |
| Feature requests | product@taxtrace.example |

---

## 11. Data Privacy & Cleanup

- All pilot data uses **synthetic** transactions
- No real client data should be uploaded
- Pilot data auto-expires after 30 days
- To delete: Settings → Danger Zone → Delete Firm Data

---

## 12. Next Steps After Pilot

1. **Review feedback** with implementation team
2. **Benchmark results** compared to targets
3. **Plan production deployment** (Stage 10)
4. **Schedule follow-up** for production onboarding

---

*Thank you for participating in the TaxTrace pilot! Your feedback directly shapes the product.*