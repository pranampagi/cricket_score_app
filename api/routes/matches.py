from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from api.database import get_db
from api import models, schemas

router = APIRouter(tags=["matches"])


@router.post("/api/matches", response_model=schemas.MatchOut)
def create_match(data: schemas.MatchCreate, db: Session = Depends(get_db)):
    match = models.Match(**data.model_dump())
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.post("/api/matches/quick", response_model=schemas.MatchOut)
def quick_match(data: schemas.QuickMatchSetup, db: Session = Depends(get_db)):
    t1 = models.Team(
        name=data.team1_name, tournament_id=data.tournament_id
    )
    t2 = models.Team(
        name=data.team2_name, tournament_id=data.tournament_id
    )
    db.add_all([t1, t2])
    db.flush()
    for name in data.team1_players:
        db.add(models.Player(name=name, team_id=t1.id))
    for name in data.team2_players:
        db.add(models.Player(name=name, team_id=t2.id))
    db.flush()
    winner_team = t1 if data.toss_winner == 1 else t2
    match = models.Match(
        tournament_id=data.tournament_id,
        team1_id=t1.id,
        team2_id=t2.id,
        overs=data.overs,
        players_per_team=data.players_per_team,
        last_man_stands=data.last_man_stands,
        toss_winner_id=winner_team.id,
        toss_decision=data.toss_decision,
        status="toss",
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/api/matches", response_model=list[schemas.MatchOut])
def list_matches(
    tournament_id: Optional[int] = None, db: Session = Depends(get_db)
):
    q = db.query(models.Match)
    if tournament_id:
        q = q.filter(models.Match.tournament_id == tournament_id)
    return q.order_by(models.Match.created_at.desc()).all()


@router.get("/api/matches/{mid}", response_model=schemas.MatchOut)
def get_match(mid: int, db: Session = Depends(get_db)):
    m = db.get(models.Match, mid)
    if not m:
        raise HTTPException(404, "Match not found")
    return m


@router.post("/api/matches/{mid}/toss", response_model=schemas.MatchOut)
def record_toss(
    mid: int, data: schemas.TossRecord, db: Session = Depends(get_db)
):
    m = db.get(models.Match, mid)
    if not m:
        raise HTTPException(404, "Match not found")
    m.toss_winner_id = data.toss_winner_id
    m.toss_decision = data.toss_decision
    m.status = "toss"
    db.commit()
    db.refresh(m)
    return m


@router.post(
    "/api/matches/{mid}/start-innings",
    response_model=schemas.InningsOut,
)
def start_innings(
    mid: int, data: schemas.InningsStart, db: Session = Depends(get_db)
):
    m = db.get(models.Match, mid)
    if not m:
        raise HTTPException(404, "Match not found")
    innings_num = m.current_innings + 1
    if innings_num == 1:
        if m.toss_decision == "bat":
            bat_id = m.toss_winner_id
            bowl_id = (
                m.team2_id
                if m.toss_winner_id == m.team1_id
                else m.team1_id
            )
        else:
            bowl_id = m.toss_winner_id
            bat_id = (
                m.team2_id
                if m.toss_winner_id == m.team1_id
                else m.team1_id
            )
    else:
        prev = (
            db.query(models.Innings)
            .filter_by(match_id=mid, innings_number=1)
            .first()
        )
        bat_id = prev.bowling_team_id
        bowl_id = prev.batting_team_id

    innings = models.Innings(
        match_id=mid,
        batting_team_id=bat_id,
        bowling_team_id=bowl_id,
        innings_number=innings_num,
    )
    if innings_num == 2:
        prev_inn = (
            db.query(models.Innings)
            .filter_by(match_id=mid, innings_number=1)
            .first()
        )
        innings.target = prev_inn.total_runs + 1
    db.add(innings)
    db.flush()

    batsmen = [data.striker_id]
    if data.non_striker_id:
        batsmen.append(data.non_striker_id)
    for pos, pid in enumerate(batsmen):
        bs = models.BattingScore(
            innings_id=innings.id,
            player_id=pid,
            batting_position=pos + 1,
            is_on_strike=(pos == 0),
            is_at_crease=True,
        )
        db.add(bs)
    bwl = models.BowlingScore(
        innings_id=innings.id,
        player_id=data.bowler_id,
        is_current_bowler=True,
    )
    db.add(bwl)
    m.current_innings = innings_num
    m.status = "live"
    db.commit()
    db.refresh(innings)
    return innings
