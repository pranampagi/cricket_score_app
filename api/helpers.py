from sqlalchemy.orm import Session, joinedload

from api import models, schemas


def finish_match(match, innings, db: Session):
    if innings.innings_number == 2:
        inn1 = (
            db.query(models.Innings)
            .options(joinedload(models.Innings.batting_team))
            .filter_by(match_id=match.id, innings_number=1)
            .first()
        )
        if innings.total_runs >= innings.target:
            match.winner_id = innings.batting_team_id
            total_possible_wkts = (
                match.players_per_team
                if match.last_man_stands
                else match.players_per_team - 1
            )
            wkts_left = total_possible_wkts - innings.total_wickets
            match.result_summary = (
                f"{innings.batting_team.name} won by {wkts_left} wickets"
            )
        else:
            runs_diff = inn1.total_runs - innings.total_runs
            match.winner_id = inn1.batting_team_id
            match.result_summary = (
                f"{inn1.batting_team.name} won by {runs_diff} runs"
            )
    match.status = "completed"


def ball_display(event):
    if event.is_wicket:
        return "W"
    if event.extras_type == "wide":
        return f"Wd+{event.extras_runs}"
    if event.extras_type == "no_ball":
        return f"Nb+{event.runs_scored}"
    if event.extras_type in ("bye", "leg_bye"):
        return f"{event.extras_type[0].upper()}+{event.extras_runs}"
    return str(event.runs_scored)


def build_batting_scoreout(b):
    return schemas.BattingScoreOut(
        id=b.id,
        player_id=b.player_id,
        player_name=b.player.name if b.player else "",
        runs=b.runs,
        balls_faced=b.balls_faced,
        fours=b.fours,
        sixes=b.sixes,
        strike_rate=b.strike_rate,
        is_out=b.is_out,
        dismissal_text=b.dismissal_text,
        batting_position=b.batting_position,
        is_on_strike=b.is_on_strike,
        is_at_crease=b.is_at_crease,
    )


def build_bowling_scoreout(b):
    return schemas.BowlingScoreOut(
        id=b.id,
        player_id=b.player_id,
        player_name=b.player.name if b.player else "",
        balls_bowled=b.balls_bowled,
        overs_display=b.overs_display,
        maidens=b.maidens,
        runs_conceded=b.runs_conceded,
        wickets=b.wickets,
        wides=b.wides,
        no_balls=b.no_balls,
        economy_rate=b.economy_rate,
        is_current_bowler=b.is_current_bowler,
    )


def build_live_state(match, innings, db: Session) -> schemas.LiveState:
    bat_scores = (
        db.query(models.BattingScore)
        .options(joinedload(models.BattingScore.player))
        .filter_by(innings_id=innings.id)
        .all()
    )
    bwl_scores = (
        db.query(models.BowlingScore)
        .options(joinedload(models.BowlingScore.player))
        .filter_by(innings_id=innings.id)
        .all()
    )
    all_events = (
        db.query(models.BallEvent).filter_by(innings_id=innings.id).all()
    )

    over_num = innings.total_balls // 6
    cur_over_events = [e for e in all_events if e.over_number == over_num]

    recent_overs = []
    for o in range(max(0, over_num - 2), over_num):
        evts = [e for e in all_events if e.over_number == o]
        total = sum(e.total_runs for e in evts)
        wkts = sum(1 for e in evts if e.is_wicket)
        recent_overs.append(
            {
                "over": o + 1,
                "runs": total,
                "wickets": wkts,
                "balls": [ball_display(e) for e in evts],
            }
        )

    overs_f = innings.total_balls / 6
    run_rate = round(innings.total_runs / overs_f, 2) if overs_f > 0 else 0.0
    req_rate = None
    if innings.innings_number == 2 and innings.target:
        rem_runs = innings.target - innings.total_runs
        rem_balls = match.overs * 6 - innings.total_balls
        req_rate = (
            round(rem_runs / (rem_balls / 6), 2) if rem_balls > 0 else None
        )

    last = all_events[-1] if all_events else None
    return schemas.LiveState(
        match=schemas.MatchOut.model_validate(match),
        innings=schemas.InningsOut.model_validate(innings),
        batting_scores=[build_batting_scoreout(b) for b in bat_scores],
        bowling_scores=[build_bowling_scoreout(b) for b in bwl_scores],
        current_over_events=[
            schemas.BallEventOut.model_validate(e) for e in cur_over_events
        ],
        recent_overs=recent_overs,
        run_rate=run_rate,
        required_rate=req_rate,
        last_event=schemas.BallEventOut.model_validate(last)
        if last
        else None,
    )
