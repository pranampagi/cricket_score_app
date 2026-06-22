from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api import models, schemas

router = APIRouter(tags=["tournaments"])


@router.post("/api/tournaments", response_model=schemas.TournamentOut)
def create_tournament(
    data: schemas.TournamentCreate, db: Session = Depends(get_db)
):
    t = models.Tournament(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/api/tournaments", response_model=list[schemas.TournamentOut])
def list_tournaments(db: Session = Depends(get_db)):
    return (
        db.query(models.Tournament)
        .order_by(models.Tournament.created_at.desc())
        .all()
    )


@router.get("/api/tournaments/{tid}", response_model=schemas.TournamentOut)
def get_tournament(tid: int, db: Session = Depends(get_db)):
    t = db.get(models.Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    return t


@router.patch("/api/tournaments/{tid}", response_model=schemas.TournamentOut)
def update_tournament(
    tid: int,
    data: schemas.TournamentUpdate,
    db: Session = Depends(get_db),
):
    t = db.get(models.Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/api/tournaments/{tid}")
def delete_tournament(tid: int, db: Session = Depends(get_db)):
    t = db.get(models.Tournament, tid)
    if not t:
        raise HTTPException(404, "Tournament not found")
    db.delete(t)
    db.commit()
    return {"ok": True}


@router.get("/api/tournaments/{tid}/standings")
def get_standings(tid: int, db: Session = Depends(get_db)):
    tournament = db.get(models.Tournament, tid)
    if not tournament:
        raise HTTPException(404, "Tournament not found")
    teams = {
        t.id: {
            "id": t.id,
            "name": t.name,
            "played": 0,
            "won": 0,
            "lost": 0,
            "tied": 0,
            "nrr": 0.0,
            "points": 0,
        }
        for t in tournament.teams
    }
    for m in tournament.matches:
        if m.status != "completed":
            continue
        if m.team1_id in teams:
            teams[m.team1_id]["played"] += 1
        if m.team2_id in teams:
            teams[m.team2_id]["played"] += 1
        if m.winner_id:
            loser_id = (
                m.team2_id
                if m.winner_id == m.team1_id
                else m.team1_id
            )
            if m.winner_id in teams:
                teams[m.winner_id]["won"] += 1
                teams[m.winner_id]["points"] += 2
            if loser_id in teams:
                teams[loser_id]["lost"] += 1
    return sorted(
        teams.values(), key=lambda x: (-x["points"], -x["won"])
    )
