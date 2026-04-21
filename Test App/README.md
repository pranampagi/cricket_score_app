# 🏏 CricScore – Cricket Scorecard App

Ball-by-ball live scoring, tournament management, and full scorecards.

## Stack
- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue 3 + Vite + Pinia + Vue Router
- **Deployment**: Vercel

## Local Development

### Backend
```bash
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn api.index:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API calls are proxied to port 8000.

## Features
- ✅ Quick match setup (5-step wizard)
- ✅ Ball-by-ball scoring: runs, extras (wide, no-ball, bye, leg-bye), wickets
- ✅ All dismissal types: bowled, caught, LBW, run-out, stumped, hit-wicket
- ✅ Live scoreboard with run rate & required run rate
- ✅ Full scorecard with batting & bowling tables
- ✅ Tournament mode (League / Knockout) with points table
- ✅ Configurable players per team (5–11) and overs (5–50)
- ✅ Responsive design (PC, tablet, smartphone)
- ✅ Dark theme, premium UI

## Deployment (Vercel)
```bash
npm i -g vercel
vercel
```

> **Note**: SQLite on Vercel uses `/tmp/` (ephemeral). For persistent data, swap in [Turso](https://turso.tech) or Supabase.
