import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api import models, schemas
from api.helpers import build_live_state, finish_match

logger = logging.getLogger(__name__)

router = APIRouter(tags=["innings"])


@router.post("/api/innings/{iid}/ball", response_model=schemas.LiveState)
def record_ball(
    iid: int, data: schemas.BallRecord, db: Session = Depends(get_db)
):
    innings = db.get(models.Innings, iid)
    if not innings:
        raise HTTPException(404, "Innings not found")
    match = db.get(models.Match, innings.match_id)

    is_wide = data.extras_type == "wide"
    is_no_ball = data.extras_type == "no_ball"
    is_legal = not is_wide and not is_no_ball

    legal_balls = innings.total_balls
    over_num = legal_balls // 6
    ball_in_over = (legal_balls % 6) + 1

    total_runs = data.runs_scored + data.extras_runs
    event = models.BallEvent(
        innings_id=iid,
        over_number=over_num,
        ball_number=ball_in_over,
        striker_id=data.striker_id,
        non_striker_id=data.non_striker_id,
        bowler_id=data.bowler_id,
        runs_scored=data.runs_scored,
        extras_type=data.extras_type,
        extras_runs=data.extras_runs,
        total_runs=total_runs,
        is_wicket=data.is_wicket,
        wicket_type=data.wicket_type,
        dismissed_player_id=data.dismissed_player_id,
        fielder_id=data.fielder_id,
        is_legal=is_legal,
    )
    db.add(event)

    innings.total_runs += total_runs
    if data.extras_type in ("wide", "no_ball", "bye", "leg_bye"):
        innings.total_extras += data.extras_runs
    if is_legal:
        innings.total_balls += 1
    if data.is_wicket:
        innings.total_wickets += 1

    bat_score = (
        db.query(models.BattingScore)
        .filter_by(innings_id=iid, player_id=data.striker_id)
        .first()
    )
    if not bat_score:
        pos = (
            db.query(models.BattingScore)
            .filter_by(innings_id=iid)
            .count()
            + 1
        )
        bat_score = models.BattingScore(
            innings_id=iid,
            player_id=data.striker_id,
            batting_position=pos,
            is_on_strike=True,
            is_at_crease=True,
        )
        db.add(bat_score)
        db.flush()
    if not is_wide:
        bat_score.balls_faced += 1
        bat_score.runs += data.runs_scored
        if data.runs_scored == 4:
            bat_score.fours += 1
        if data.runs_scored == 6:
            bat_score.sixes += 1

    if data.is_wicket and data.dismissed_player_id:
        dismissed = (
            db.query(models.BattingScore)
            .filter_by(
                innings_id=iid, player_id=data.dismissed_player_id
            )
            .first()
        )
        if dismissed:
            dismissed.is_out = True
            dismissed.is_at_crease = False
            dismissed.is_on_strike = False
            wtype = data.wicket_type or "out"
            fielder = (
                db.get(models.Player, data.fielder_id)
                if data.fielder_id
                else None
            )
            bowler = db.get(models.Player, data.bowler_id)
            if wtype == "caught":
                dismissed.dismissal_text = (
                    f"c {fielder.name if fielder else '?'} b {bowler.name}"
                )
            elif wtype == "bowled":
                dismissed.dismissal_text = f"b {bowler.name}"
            elif wtype == "lbw":
                dismissed.dismissal_text = f"lbw b {bowler.name}"
            elif wtype == "run_out":
                dismissed.dismissal_text = (
                    f"run out ({fielder.name if fielder else '?'})"
                )
            elif wtype == "stumped":
                dismissed.dismissal_text = f"st {fielder.name if fielder else '?'} b {bowler.name}"
            elif wtype == "hit_wicket":
                dismissed.dismissal_text = f"hit wicket b {bowler.name}"
            else:
                dismissed.dismissal_text = wtype

    bwl_score = (
        db.query(models.BowlingScore)
        .filter_by(innings_id=iid, player_id=data.bowler_id)
        .first()
    )
    if not bwl_score:
        bwl_score = models.BowlingScore(
            innings_id=iid,
            player_id=data.bowler_id,
            is_current_bowler=True,
        )
        db.add(bwl_score)
        db.flush()
    bwl_score.runs_conceded += data.runs_scored + (
        data.extras_runs
        if data.extras_type in ("wide", "no_ball")
        else 0
    )
    if is_legal:
        bwl_score.balls_bowled += 1
    if is_wide:
        bwl_score.wides += 1
    if is_no_ball:
        bwl_score.no_balls += 1
    if data.is_wicket and data.wicket_type not in ("run_out",):
        bwl_score.wickets += 1

    rotate = (data.runs_scored % 2 == 1) and not is_wide
    new_legal = innings.total_balls
    end_of_over = is_legal and (new_legal % 6 == 0)
    if end_of_over:
        rotate = not rotate

    # --- Maiden over tracking ---
    if end_of_over:
        over_events = (
            db.query(models.BallEvent)
            .filter_by(
                innings_id=iid,
                over_number=over_num,
                bowler_id=data.bowler_id,
            )
            .all()
        )
        over_runs = sum(e.total_runs for e in over_events)
        if over_runs == 0:
            bwl_score.maidens += 1

    if rotate:
        striker_bs = (
            db.query(models.BattingScore)
            .filter_by(innings_id=iid, player_id=data.striker_id)
            .first()
        )
        non_striker_id = data.non_striker_id
        if not non_striker_id:
            other = (
                db.query(models.BattingScore)
                .filter(
                    models.BattingScore.innings_id == iid,
                    models.BattingScore.is_at_crease == True,
                    models.BattingScore.player_id != data.striker_id,
                )
                .first()
            )
            if other:
                non_striker_id = other.player_id

        if non_striker_id:
            non_striker_bs = (
                db.query(models.BattingScore)
                .filter_by(innings_id=iid, player_id=non_striker_id)
                .first()
            )
            if striker_bs and non_striker_bs:
                striker_bs.is_on_strike = False
                non_striker_bs.is_on_strike = True

    at_crease = (
        db.query(models.BattingScore)
        .filter_by(innings_id=iid, is_at_crease=True)
        .all()
    )
    if len(at_crease) == 1:
        at_crease[0].is_on_strike = True
    elif len(at_crease) > 1:
        on_strike = [b for b in at_crease if b.is_on_strike]
        if not on_strike:
            at_crease[0].is_on_strike = True

    max_wickets = (
        match.players_per_team
        if match.last_man_stands
        else match.players_per_team - 1
    )
    max_balls = match.overs * 6
    innings_over = innings.total_wickets >= max_wickets or (
        is_legal and innings.total_balls >= max_balls
    )
    if innings_over:
        innings.is_completed = True
        if innings.innings_number == 1:
            match.status = "innings_break"
        else:
            finish_match(match, innings, db)

    if (
        innings.innings_number == 2
        and innings.target
        and innings.total_runs >= innings.target
    ):
        innings.is_completed = True
        finish_match(match, innings, db)

    db.commit()
    return build_live_state(match, innings, db)


@router.post("/api/innings/{iid}/undo", response_model=schemas.LiveState)
def undo_ball(iid: int, db: Session = Depends(get_db)):
    try:
        innings = db.get(models.Innings, iid)
        if not innings:
            raise HTTPException(404, "Innings not found")
        match = db.get(models.Match, innings.match_id)

        last_event = (
            db.query(models.BallEvent)
            .filter_by(innings_id=iid)
            .order_by(models.BallEvent.id.desc())
            .first()
        )
        if not last_event:
            raise HTTPException(400, "No balls to undo in this innings")

        is_wide = last_event.extras_type == "wide"
        is_legal = last_event.is_legal

        innings.total_runs = max(
            0, innings.total_runs - last_event.total_runs
        )
        if last_event.extras_type:
            innings.total_extras = max(
                0, innings.total_extras - last_event.extras_runs
            )
        if is_legal:
            innings.total_balls = max(0, innings.total_balls - 1)
        if last_event.is_wicket:
            innings.total_wickets = max(0, innings.total_wickets - 1)

        if innings.is_completed:
            innings.is_completed = False
            match.status = "live"
            match.winner_id = None
            match.result_summary = None

        crease_batsmen = (
            db.query(models.BattingScore)
            .filter_by(innings_id=iid, is_at_crease=True)
            .all()
        )
        for b in crease_batsmen:
            if b.player_id not in (
                last_event.striker_id,
                last_event.non_striker_id,
            ):
                db.delete(b)

        striker_bs = (
            db.query(models.BattingScore)
            .filter_by(
                innings_id=iid, player_id=last_event.striker_id
            )
            .first()
        )
        if striker_bs:
            striker_bs.is_at_crease = True
            striker_bs.is_on_strike = True
            striker_bs.is_out = False
            striker_bs.dismissal_text = None
            if not is_wide:
                striker_bs.balls_faced = max(
                    0, striker_bs.balls_faced - 1
                )
                striker_bs.runs = max(
                    0, striker_bs.runs - last_event.runs_scored
                )
                if last_event.runs_scored == 4:
                    striker_bs.fours = max(
                        0, striker_bs.fours - 1
                    )
                if last_event.runs_scored == 6:
                    striker_bs.sixes = max(
                        0, striker_bs.sixes - 1
                    )

        if last_event.non_striker_id:
            ns_bs = (
                db.query(models.BattingScore)
                .filter_by(
                    innings_id=iid,
                    player_id=last_event.non_striker_id,
                )
                .first()
            )
            if ns_bs:
                ns_bs.is_at_crease = True
                ns_bs.is_on_strike = False
                ns_bs.is_out = False
                ns_bs.dismissal_text = None

        db.query(models.BowlingScore).filter_by(
            innings_id=iid
        ).update({"is_current_bowler": False})
        bwl_score = (
            db.query(models.BowlingScore)
            .filter_by(
                innings_id=iid, player_id=last_event.bowler_id
            )
            .first()
        )
        if bwl_score:
            bwl_score.is_current_bowler = True
            conceded = last_event.runs_scored
            if last_event.extras_type in ("wide", "no_ball"):
                conceded += last_event.extras_runs
            bwl_score.runs_conceded = max(
                0, bwl_score.runs_conceded - conceded
            )
            if is_legal:
                bwl_score.balls_bowled = max(
                    0, bwl_score.balls_bowled - 1
                )
            if last_event.extras_type == "wide":
                bwl_score.wides = max(0, bwl_score.wides - 1)
            if last_event.extras_type == "no_ball":
                bwl_score.no_balls = max(
                    0, bwl_score.no_balls - 1
                )
            if (
                last_event.is_wicket
                and last_event.wicket_type not in ("run_out",)
            ):
                bwl_score.wickets = max(
                    0, bwl_score.wickets - 1
                )

            if is_legal and last_event.ball_number == 6:
                remaining_over_events = (
                    db.query(models.BallEvent)
                    .filter_by(
                        innings_id=iid,
                        over_number=last_event.over_number,
                        bowler_id=last_event.bowler_id,
                    )
                    .all()
                )
                total_over_runs = sum(
                    e.total_runs for e in remaining_over_events
                )
                if total_over_runs > 0 and bwl_score.maidens > 0:
                    bwl_score.maidens -= 1

        db.delete(last_event)
        db.commit()
        db.refresh(match)
        db.refresh(innings)

        return build_live_state(match, innings, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to undo ball in innings %s", iid)
        raise HTTPException(500, f"Failed to undo ball: {str(e)}")


@router.post("/api/innings/{iid}/next-bowler")
def set_next_bowler(
    iid: int, bowler_id: int, db: Session = Depends(get_db)
):
    db.query(models.BowlingScore).filter_by(innings_id=iid).update(
        {"is_current_bowler": False}
    )
    bwl = (
        db.query(models.BowlingScore)
        .filter_by(innings_id=iid, player_id=bowler_id)
        .first()
    )
    if not bwl:
        innings = db.get(models.Innings, iid)
        bwl = models.BowlingScore(
            innings_id=iid,
            player_id=bowler_id,
            is_current_bowler=True,
        )
        db.add(bwl)
    else:
        bwl.is_current_bowler = True
    db.commit()
    return {"ok": True}


@router.post("/api/innings/{iid}/next-batsman")
def set_next_batsman(
    iid: int,
    player_id: int,
    on_strike: bool = True,
    db: Session = Depends(get_db),
):
    innings = db.get(models.Innings, iid)
    pos = (
        db.query(models.BattingScore)
        .filter_by(innings_id=iid)
        .count()
        + 1
    )
    bs = models.BattingScore(
        innings_id=iid,
        player_id=player_id,
        batting_position=pos,
        is_on_strike=on_strike,
        is_at_crease=True,
    )
    db.add(bs)
    db.commit()
    return {"ok": True}
