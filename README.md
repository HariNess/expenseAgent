# 💼 NessExpense Agent — NessAthon 2026

An intelligent multi-agent expense management system built with Python, FastAPI, Claude AI, and React.

---

## 🏗️ Architecture

```
User (Web or Teams)
        │
        ▼
┌─────────────────────┐
│  Orchestrator Agent │  Claude Sonnet — understands intent
│  (orchestrator.py)  │  routes to specialist agents
└────────┬────────────┘
         │
    ┌────┼──────────────────────┐
    ▼    ▼                      ▼
Extraction  Fraud Detection  Approval
Agent       Agent            Agent
(Claude     (Rules + AI)     (SQLite +
 Vision)                      Routing)
         │
         ▼
      SQLite DB
   (expenses, employees,
    approval_log)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Anthropic API Key

### 1. Clone and setup

```bash
git clone <repo>
cd nessathon
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### 2. Start Backend

```bash
chmod +x start_backend.sh
./start_backend.sh
```

Backend runs at: http://localhost:8081
API docs at: http://localhost:8081/docs

### 3. Start Frontend

```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

Frontend runs at: http://localhost:8080

---

## 📁 Project Structure

```
nessathon/
├── backend/
│   ├── main.py                    # FastAPI app entry
│   ├── agents/
│   │   ├── orchestrator.py        # Master Claude agent
│   │   ├── extraction_agent.py    # Invoice OCR via Claude Vision
│   │   ├── fraud_agent.py         # Fraud detection (rules + AI)
│   │   └── approval_agent.py      # Approval routing & logging
│   ├── models/
│   │   ├── database.py            # SQLite + SQLAlchemy
│   │   └── schemas.py             # Pydantic models
│   ├── routers/
│   │   ├── chat.py                # Chat & upload endpoints
│   │   └── approvals.py           # Approval endpoints
│   ├── services/
│   │   └── claude_service.py      # Claude API wrapper
│   └── utils/
│       ├── fraud_checks.py        # Rule-based fraud checks
│       └── helpers.py             # Utility functions
├── frontend/
│   └── src/
│       ├── App.jsx                # Main app with sidebar
│       ├── components/
│       │   ├── ChatWindow.jsx     # Chat interface
│       │   ├── MessageBubble.jsx  # Message rendering
│       │   ├── ExpenseTable.jsx   # Editable invoice table
│       │   ├── FileUpload.jsx     # File upload component
│       │   └── ApprovalPanel.jsx  # Manager/HR approval UI
│       └── utils/api.js           # API calls
├── database/
│   └── nessexpense.db             # SQLite database (auto-created)
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🤖 Multi-Agent System

| Agent | Responsibility |
|---|---|
| **Orchestrator** | Understands user intent, manages conversation flow |
| **Extraction** | Claude Vision — reads invoices and extracts structured data |
| **Fraud Detection** | 4 rule checks + AI anomaly detection |
| **Approval** | Routes expenses, manages approval workflow |

---

## 🔍 Fraud Detection Checks

1. **Duplicate Invoice** — Same invoice number already submitted
2. **15-Day Rule** — Invoice older than 15 days rejected
3. **GST Validation** — Missing GST number flagged
4. **Amount Validity** — Zero or negative amounts rejected
5. **AI Analysis** — Claude analyzes patterns for anomalies

---

## 💰 Approval Flow

```
Amount < ₹5,000  → Auto-approved instantly
Amount ≥ ₹5,000  → Manager approval → HR approval → Done
```

All approvals happen in the background. Chat never freezes.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat/message` | Send chat message |
| POST | `/api/chat/upload-invoice` | Upload invoice file |
| POST | `/api/chat/submit-expense` | Submit confirmed expense |
| POST | `/api/chat/edit-field` | Edit extracted field |
| GET | `/api/chat/status/{id}` | Get expense status |
| GET | `/api/chat/my-expenses/{email}` | Get user's expenses |
| GET | `/api/approvals/pending/{email}` | Get pending approvals |
| POST | `/api/approvals/action` | Take approval action |
| GET | `/api/approvals/all-expenses` | Admin: all expenses |

---

## 👥 Demo Users

| Name | Email | Role |
|---|---|---|
| Hariharasudan V. | hari@ness.com | Employee |
| Atharva Bhagat | atharva@ness.com | Employee |
| Vignesh Jayakumar | vignesh@ness.com | Manager |
| HR Manager | hr@ness.com | HR |

---

## 🧪 Demo Script (Hackathon)

1. Open app as **Hariharasudan** (employee)
2. Upload a fuel invoice image
3. Watch extraction + fraud check happen live
4. Edit category if needed
5. Submit → since amount ≥ ₹5,000, goes to manager
6. Switch to **Vignesh** (manager) → Approvals tab
7. Approve the expense
8. Switch to **HR Manager** → Approvals tab
9. Final HR approval
10. Switch back to Hariharasudan → see fully approved status

**Total demo time: ~90 seconds** 🎯

---

## 🏆 Built for NessAthon 2026

Team: Vignesh Jayakumar · Atharva Bhagat · Hariharasudan Venkatasalam
# expenseAgent
