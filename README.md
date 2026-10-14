# 🥬 FreshRoute — Smart Perishable Produce Distribution

A decision-support dashboard that optimizes perishable produce distribution using a deterministic, rule-based heuristic with dynamic scenario generation. Built for hackathon speed with an explainable, professional UI.

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
2. The dashboard automatically loads a dynamic produce scenario and optimizes it immediately.
3. Click **"🎲 New Scenario"** to generate a brand new situation with random archetypes and watch the charts and dispatches adapt live.
4. Use **"Replay seed"** to enter any seed number (e.g. `12345`) and reproduce the exact same scenario and mathematical results.

---

## Dynamic Scenario Generator & Archetypes

FreshRoute features a dynamic scenario generator ([scenario_generator.py](file:///c:/Users/ajoya/Downloads/FreshRoute/backend/scenario_generator.py)) with zero hardcoded datasets. Scenarios select one of 6 real-world operational archetypes:

1. **Normal Week** — Balanced supply corridors and steady market baseline.
2. **Peak Harvest Glut** — Bumper farm yields (+60% batch volume, -30% market prices).
3. **Festival Demand Surge** — Urban festive pull (+70% destination demand, +30% market prices).
4. **Fuel Price Spike** — High diesel inflation (2× freight transit costs per km).
5. **Monsoon Road Delays** — Waterlogged highways (+40% transit distance and delay risks).
6. **Cold Chain Failure** — Refrigeration breakdown (40% of batches suffer a 50% shelf-life cut).

### Engineering Reproducibility
Every scenario is driven by an integer seed:
- Calling `GET /api/scenario` generates a random seed and returns it in the payload.
- Calling `GET /api/scenario?seed=12345` reproduces the exact same batches, destinations, trucks, and optimization decisions.

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python, FastAPI, SQLAlchemy       |
| Database   | SQLite (`freshroute.db`)          |
| Engine     | Deterministic Heuristic Optimizer |
| Frontend   | React 18, Vite, Tailwind CSS     |
| Charts     | Recharts                          |
| Icons      | Lucide React                      |

## Architecture

```
FreshRoute/
├── backend/
│   ├── main.py                # FastAPI endpoints (scenario, optimize, batches, destinations)
│   ├── scenario_generator.py  # Dynamic scenario generator with 6 archetypes & seed replay
│   ├── optimizer.py           # Core heuristic with fleet capacity & zero-division guards
│   ├── models.py              # Pydantic & SQLAlchemy models
│   ├── database.py            # SQLite connection setup
│   ├── seed.py                # Dynamic SQLite seeder (no static lists)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main dashboard, scenario banner, live seed replay controls
│   │   └── components/
│   │       ├── SummaryCards.jsx     # KPI metric cards with NaN/Infinity guards
│   │       ├── ComparisonChart.jsx  # Recharts Baseline vs Optimized comparison
│   │       └── DispatchTable.jsx    # Dispatch plan table with reasons & discount badges
│   ├── package.json
│   ├── vite.config.js         # Vite dev server + proxy to backend
│   └── tailwind.config.js
└── README.md
```

## API Endpoints

| Method | Endpoint                        | Description                                                         |
|--------|---------------------------------|---------------------------------------------------------------------|
| GET    | `/api/scenario?seed=<optional>` | Generates a dynamic scenario with archetype and seed reproducibility |
| POST   | `/api/optimize`                 | Optimizes the payload scenario or falls back to active scenario     |
| GET    | `/api/batches`                  | Returns active batches                                              |
| GET    | `/api/destinations`             | Returns active destinations                                         |
| POST   | `/api/seed?seed=<optional>`     | Seeds SQLite with a dynamic scenario                                |

---

*No complex AI black boxes, no Docker requirements — purely deterministic, explainable, and reproducible.*
