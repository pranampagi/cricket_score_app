from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import init_db
from api.routes import tournaments, matches, innings, scorecard, teams

app = FastAPI(title="Cricket Scorer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tournaments.router)
app.include_router(matches.router)
app.include_router(innings.router)
app.include_router(scorecard.router)
app.include_router(teams.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
