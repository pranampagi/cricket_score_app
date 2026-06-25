from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api import models, schemas
from api.helpers import (
    build_batting_scoreout,
    build_bowling_scoreout,
    build_live_state,
)

router = APIRouter(tags=["scorecard"])


@router.get("/api/innings/{iid}/live", response_model=schemas.LiveState)
def get_live(iid: int, db: Session = Depends(get_db)):
    innings = db.get(models.Innings, iid)
    if not innings:
        raise HTTPException(404, "Innings not found")
    match = db.get(models.Match, innings.match_id)
    return build_live_state(match, innings, db)


@router.get("/api/matches/{mid}/live", response_model=schemas.LiveState)
def get_match_live(mid: int, db: Session = Depends(get_db)):
    match = db.get(models.Match, mid)
    if not match:
        raise HTTPException(404, "Match not found")
    innings = (
        db.query(models.Innings)
        .filter_by(match_id=mid, innings_number=match.current_innings)
        .first()
    )
    if not innings:
        raise HTTPException(404, "No innings started yet")
    return build_live_state(match, innings, db)


@router.get(
    "/api/matches/{mid}/scorecard",
    response_model=schemas.FullScorecard,
)
def get_scorecard(mid: int, db: Session = Depends(get_db)):
    match = db.get(models.Match, mid)
    if not match:
        raise HTTPException(404, "Match not found")
    all_innings = (
        db.query(models.Innings)
        .filter_by(match_id=mid)
        .order_by(models.Innings.innings_number)
        .all()
    )
    innings_list = []
    for inn in all_innings:
        bat_scores = (
            db.query(models.BattingScore)
            .filter_by(innings_id=inn.id)
            .order_by(models.BattingScore.batting_position)
            .all()
        )
        bwl_scores = (
            db.query(models.BowlingScore)
            .filter_by(innings_id=inn.id)
            .all()
        )
        overs_f = inn.total_balls // 6
        rem = inn.total_balls % 6
        overs_display = f"{overs_f}.{rem}"
        innings_list.append(
            schemas.ScorecardInnings(
                innings=schemas.InningsOut.model_validate(inn),
                batting_team=schemas.TeamBrief.model_validate(
                    inn.batting_team
                ),
                bowling_team=schemas.TeamBrief.model_validate(
                    inn.bowling_team
                ),
                batting_scores=[
                    build_batting_scoreout(b, db) for b in bat_scores
                ],
                bowling_scores=[
                    build_bowling_scoreout(b, db) for b in bwl_scores
                ],
                fall_of_wickets=[],
                overs_display=overs_display,
            )
        )
    return schemas.FullScorecard(
        match=schemas.MatchOut.model_validate(match),
        innings_list=innings_list,
    )
