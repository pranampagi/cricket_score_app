from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api import models, schemas

router = APIRouter(tags=["teams"])


@router.post("/api/teams", response_model=schemas.TeamOut)
def create_team(data: schemas.TeamCreate, db: Session = Depends(get_db)):
    team = models.Team(**data.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/api/teams/{team_id}", response_model=schemas.TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Team, team_id)
    if not t:
        raise HTTPException(404, "Team not found")
    return t


@router.delete("/api/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Team, team_id)
    if not t:
        raise HTTPException(404, "Team not found")
    db.delete(t)
    db.commit()
    return {"ok": True}


@router.post("/api/players", response_model=schemas.PlayerOut)
def create_player(data: schemas.PlayerCreate, db: Session = Depends(get_db)):
    p = models.Player(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/api/players/{pid}")
def delete_player(pid: int, db: Session = Depends(get_db)):
    p = db.get(models.Player, pid)
    if not p:
        raise HTTPException(404, "Player not found")
    db.delete(p)
    db.commit()
    return {"ok": True}
