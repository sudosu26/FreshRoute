# 🥬 FreshRoute — Smart Perishable Produce Distribution

A high-performance decision-support dashboard that optimizes perishable produce distribution using a deterministic, rule-based heuristic with dynamic scenario generation. Built for hackathon speed with an explainable, professional UI.

## Quick Start (Windows)

### 1. Start the Backend (Terminal 1)

```powershell
cd backend
py -m pip install -r requirements.txt
py -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at **http://localhost:8000**. The database is auto-seeded dynamically on first run.

### 2. Start the Frontend (Terminal 2)

```powershell
cd frontend
npm install
npm run dev
```

> **Note:** If you get an execution policy error on Windows, run:
> ```powershell
> powershell -ExecutionPolicy Bypass -Command "npm run dev"
> ```

The dashboard will be available at **http://localhost:5173**.

### 3. Using the Live Demo

1. Open **http://localhost:5173** in your browser.
2. The dashboard automatically simulates corridors and renders the optimized dispatch plan.
3. Select any archetype from the dropdown (e.g. **Cold Chain Failure**, **Monsoon Road Delays**, or **🎲 Random**) to test disruptions.
4. Click **"🎲 New Scenario"** to generate new distributions live.
5. Use **"Replay seed"** to enter any seed number (e.g. `77777`) and reproduce the exact same scenario and mathematical results.
6. In the Dispatch Table, use the interactive search bar and filter tabs (**Markdown Deals**, **Full Price**, **Unallocated**) to inspect decisions.

---

## Performance & Architecture Optimizations

- **Single Round-Trip Loading (`GET /api/scenario?include_optimization=true`):** Fetches the scenario and executes the heuristic plan in a single request, cutting network latency by 50%.
- **Vite Rollup Chunk Splitting:** Recharts, React, and Lucide React are segregated into independent vendor chunks, shrinking main bundle size down to 26 kB for instant page load.
- **SQLite WAL Mode:** Enabled Write-Ahead Logging and `PRAGMA synchronous=NORMAL` for concurrent, non-blocking database queries.
- **Explainable Dispatch Decisions:** Every allocation has an explainable reason (e.g. *"Priority dispatch — shortest shelf life (1.5d), routed to nearby Pune Metro"*).
- **Interactive UI UX:** Added client-side text search, quick-filter tabs, column sorting, and copyable audit hash buttons.

---

## Dynamic Scenario Archetypes

FreshRoute features a dynamic scenario generator ([scenario_generator.py](file:///c:/Users/ajoya/Downloads/FreshRoute/backend/scenario_generator.py)) with zero hardcoded datasets:

1. **Normal Week** — Balanced supply corridors and steady market baseline.
2. **Peak Harvest Glut** — Bumper farm yields (+60% batch volume, -30% market prices).
3. **Festival Demand Surge** — Urban festive pull (+70% destination demand, +30% market prices).
4. **Fuel Price Spike** — High diesel inflation (2× freight transit costs per km).
5. **Monsoon Road Delays** — Waterlogged highways (+40% transit distance and delay risks).
6. **Cold Chain Failure** — Refrigeration breakdown (40% of batches suffer a 50% shelf-life cut).

---

## Tech Stack

| Layer      | Technology                                    |
|------------|-----------------------------------------------|
| Backend    | Python, FastAPI, SQLAlchemy (WAL Mode)        |
| Database   | SQLite (`freshroute.db`)                      |
| Engine     | Deterministic Heuristic Optimizer             |
| Frontend   | React 18, Vite (Code Split), Tailwind CSS     |
| Charts     | Recharts                                      |
| Icons      | Lucide React                                  |

---

*No complex AI black boxes, no Docker requirements — purely deterministic, explainable, and reproducible.*
