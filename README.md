# Phoenix CAP Policy Analysis App

The Phoenix CAP Policy Analysis App is a multi-agent Generative AI web application built for the ASU Sustainable Urban Resilience for the Future (SURE) research program. It enables policymakers, researchers, and community members to submit climate policy ideas and receive a rigorous, evidence-based evaluation against the City of Phoenix 2021 Climate Action Plan (CAP). Using a sequential pipeline of specialized Claude AI agents, the app assesses each idea across seven weighted criteria—effectiveness, efficiency, equity, liberty, political feasibility, social acceptability, and administrative feasibility—producing a formal policy memorandum with CAP citations, a phased implementation roadmap, and (in full mode) multi-stakeholder evaluator perspectives synthesized into a final readiness verdict.

---

## Architecture

```
User (Browser)
      │  idea + weights
      ▼
┌─────────────────────────────────────────────────────────────┐
│                     React + Vite Frontend                   │
│  IdeaInput → WeightSliders → PipelineStatus → ResultsView  │
│           AgentOutput | MemoPanel | EvidencePanel           │
└──────────────────────┬──────────────────────────────────────┘
                       │  POST /api/run
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)               │
│                                                             │
│  orchestrator.run_pipeline()                                │
│                                                             │
│  MVP mode:                                                  │
│    Stage 1 (Assessment) ──► Stage 2 (Planning)              │
│                                    └──► Stage 4 (Memo)      │
│                                                             │
│  Full mode:                                                 │
│    Stage 1 ──► Stage 2 ──► Stage 3a (Neutral Evaluator)    │
│                            Stage 3b (Citizen Evaluator)     │
│                            Stage 3c (ADEQ Evaluator)        │
│                                    └──► Stage 5 (Synthesis) │
│                                              └──► Stage 4   │
└──────────────────────┬──────────────────────────────────────┘
                       │  Anthropic Claude API
                       ▼
              claude-sonnet-4-5
```

---

## Setup Instructions

### 1. Install Python dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Install frontend dependencies
```bash
cd frontend && npm install
```

### 3. Configure your API key
```bash
cp .env.example .env
# Open .env and set:
#   ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Place the CAP text file in data/
The PDF is already included. Extract text to `data/2021_Phoenix_CAP.txt`:
```bash
python scripts/extract_cap.py
```

### 5. Run the app
```bash
bash run.sh
```

- **Frontend:** http://localhost:5173  
- **Backend:**  http://localhost:8000  
- **API docs:** http://localhost:8000/docs

---

## How It Works

| Stage | Agent | Description |
|-------|-------|-------------|
| **Stage 1** | Assessment Agent | Evaluates the idea against CAP goals across five dimensions: existing alignment, potential conflicts, equity implications, feasibility, and implementation pathway. Returns citations and an overall verdict. |
| **Stage 2** | Planning Agent | Produces a phased implementation roadmap with quick wins (0–12 months), medium-term milestones (1–3 years), long-term goals (3–5 years), and an equity checklist. |
| **Stage 3a** | Neutral Policy Evaluator | Scores the idea against all seven weighted criteria from an objective policy-analysis perspective, citing CAP text as evidence. *(Full mode only)* |
| **Stage 3b** | Citizen Evaluator | Evaluates the idea from the perspective of Phoenix residents, focusing on equity, livability, and community impact. *(Full mode only)* |
| **Stage 3c** | ADEQ Evaluator | Assesses environmental compliance, regulatory alignment, and state-agency feasibility from an Arizona DEQ perspective. *(Full mode only)* |
| **Stage 5** | Synthesis Agent | Reconciles the three evaluator reports into consensus findings, divergent concerns, priority revisions, and an overall readiness rating. *(Full mode only)* |
| **Stage 4** | Policy Memo Agent | Writes a formal one-page executive policy memorandum (400–450 words) addressed to the appropriate recipient, incorporating all prior stage findings and CAP citations. |

---

## Evaluation Criteria (Chapter 6, Figure 6-1)

| # | Criterion | Description | Weight (0–10) |
|---|-----------|-------------|---------------|
| 1 | **Effectiveness** | Does the policy achieve its stated climate/sustainability goals? | User-set |
| 2 | **Efficiency** | Is it cost-effective and resource-efficient relative to alternatives? | User-set |
| 3 | **Equity** | Does it distribute benefits and burdens fairly across all communities? | User-set |
| 4 | **Liberty / Freedom** | Does it respect individual rights and minimize coercive mandates? | User-set |
| 5 | **Political Feasibility** | Can it gain sufficient political support to be adopted and sustained? | User-set |
| 6 | **Social Acceptability** | Will residents, businesses, and civil society broadly support it? | User-set |
| 7 | **Administrative Feasibility** | Can the City of Phoenix realistically implement and enforce it? | User-set |

---

## Project Structure

```
backend/
  main.py           – FastAPI entry point + lifespan
  config.py         – Settings loaded from .env
  cap_text.py       – CAP text loader (lru_cache)
  schemas.py        – Pydantic v2 models for all stages
  orchestrator.py   – Pipeline coordinator (MVP & Full modes)
  exporter.py       – .docx / .md export helpers
  agents/           – One module per pipeline stage
  prompts/          – System + user prompt templates per stage

frontend/
  vite.config.js    – Vite config with /api proxy to port 8000
  src/
    App.jsx         – Root component, routing, and pipeline orchestration
    api/client.js   – Fetch wrapper for the FastAPI backend
    components/     – IdeaInput, WeightSliders, PipelineStatus,
                      AgentOutput, MemoPanel, EvaluatorPanel,
                      EvidencePanel

data/
  2021_Phoenix_CAP_compressed.pdf  – Source PDF
  2021_Phoenix_CAP.txt             – Extracted text (generated by setup)

scripts/
  extract_cap.py    – One-time PDF → .txt extraction
  setup.sh          – Full first-time setup automation
```
