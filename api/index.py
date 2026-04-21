from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

from api.database import get_db, init_db
from api import models, schemas

app = FastAPI(title="Cricket Scorer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# ── Health ──────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}

# ── Tournaments ─────────────────────────────────────────────────
@app.post("/api/tournaments", response_model=schemas.TournamentOut)
def create_tournament(data: schemas.TournamentCreate, db: Session = Depends(get_db)):
    t = models.Tournament(**data.model_dump())
    db.add(t); db.commit(); db.refresh(t)
    return t

@app.get("/api/tournaments", response_model=list[schemas.TournamentOut])
def list_tournaments(db: Session = Depends(get_db)):
    return db.query(models.Tournament).order_by(models.Tournament.created_at.desc()).all()

@app.get("/api/tournaments/{tid}", response_model=schemas.TournamentOut)
def get_tournament(tid: int, db: Session = Depends(get_db)):
    t = db.get(models.Tournament, tid)
    if not t: raise HTTPException(404, "Not found")
    return t

@app.patch("/api/tournaments/{tid}", response_model=schemas.TournamentOut)
def update_tournament(tid: int, data: schemas.TournamentUpdate, db: Session = Depends(get_db)):
    t = db.get(models.Tournament, tid)
    if not t: raise HTTPException(404, "Not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    db.commit(); db.refresh(t)
    return t

@app.delete("/api/tournaments/{tid}")
def delete_tournament(tid: int, db: Session = Depends(get_db)):
    t = db.get(models.Tournament, tid)
    if not t: raise HTTPException(404, "Not found")
    db.delete(t); db.commit()
    return {"ok": True}

# ── Teams ───────────────────────────────────────────────────────
@app.post("/api/teams", response_model=schemas.TeamOut)
def create_team(data: schemas.TeamCreate, db: Session = Depends(get_db)):
    team = models.Team(**data.model_dump())
    db.add(team); db.commit(); db.refresh(team)
    return team

@app.get("/api/teams/{team_id}", response_model=schemas.TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Team, team_id)
    if not t: raise HTTPException(404, "Not found")
    return t

@app.delete("/api/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    t = db.get(models.Team, team_id)
    if not t: raise HTTPException(404, "Not found")
    db.delete(t); db.commit()
    return {"ok": True}

# ── Players ─────────────────────────────────────────────────────
@app.post("/api/players", response_model=schemas.PlayerOut)
def create_player(data: schemas.PlayerCreate, db: Session = Depends(get_db)):
    p = models.Player(**data.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p

@app.delete("/api/players/{pid}")
def delete_player(pid: int, db: Session = Depends(get_db)):
    p = db.get(models.Player, pid)
    if not p: raise HTTPException(404, "Not found")
    db.delete(p); db.commit()
    return {"ok": True}

# ── Matches ─────────────────────────────────────────────────────
@app.post("/api/matches/quick", response_model=schemas.MatchOut)
def quick_match(data: schemas.QuickMatchSetup, db: Session = Depends(get_db)):
    t1 = models.Team(name=data.team1_name, tournament_id=data.tournament_id)
    t2 = models.Team(name=data.team2_name, tournament_id=data.tournament_id)
    db.add_all([t1, t2]); db.flush()
    for name in data.team1_players:
        db.add(models.Player(name=name, team_id=t1.id))
    for name in data.team2_players:
        db.add(models.Player(name=name, team_id=t2.id))
    db.flush()
    winner_team = t1 if data.toss_winner == 1 else t2
    match = models.Match(
        tournament_id=data.tournament_id,
        team1_id=t1.id, team2_id=t2.id,
        overs=data.overs, players_per_team=data.players_per_team,
        last_man_stands=data.last_man_stands,
        toss_winner_id=winner_team.id,
        toss_decision=data.toss_decision,
        status="toss"
    )
    db.add(match); db.commit(); db.refresh(match)
    return match

@app.post("/api/matches", response_model=schemas.MatchOut)
def create_match(data: schemas.MatchCreate, db: Session = Depends(get_db)):
    match = models.Match(**data.model_dump())
    db.add(match); db.commit(); db.refresh(match)
    return match

@app.get("/api/matches", response_model=list[schemas.MatchOut])
def list_matches(tournament_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(models.Match)
    if tournament_id:
        q = q.filter(models.Match.tournament_id == tournament_id)
    return q.order_by(models.Match.created_at.desc()).all()

@app.get("/api/matches/{mid}", response_model=schemas.MatchOut)
def get_match(mid: int, db: Session = Depends(get_db)):
    m = db.get(models.Match, mid)
    if not m: raise HTTPException(404, "Not found")
    return m

@app.post("/api/matches/{mid}/toss", response_model=schemas.MatchOut)
def record_toss(mid: int, data: schemas.TossRecord, db: Session = Depends(get_db)):
    m = db.get(models.Match, mid)
    if not m: raise HTTPException(404)
    m.toss_winner_id = data.toss_winner_id
    m.toss_decision = data.toss_decision
    m.status = "toss"
    db.commit(); db.refresh(m)
    return m

@app.post("/api/matches/{mid}/start-innings", response_model=schemas.InningsOut)
def start_innings(mid: int, data: schemas.InningsStart, db: Session = Depends(get_db)):
    m = db.get(models.Match, mid)
    if not m: raise HTTPException(404)
    innings_num = m.current_innings + 1
    # Determine batting/bowling teams
    if innings_num == 1:
        if m.toss_decision == "bat":
            bat_id = m.toss_winner_id
            bowl_id = m.team2_id if m.toss_winner_id == m.team1_id else m.team1_id
        else:
            bowl_id = m.toss_winner_id
            bat_id = m.team2_id if m.toss_winner_id == m.team1_id else m.team1_id
    else:
        prev = db.query(models.Innings).filter_by(match_id=mid, innings_number=1).first()
        bat_id = prev.bowling_team_id
        bowl_id = prev.batting_team_id

    innings = models.Innings(
        match_id=mid, batting_team_id=bat_id,
        bowling_team_id=bowl_id, innings_number=innings_num
    )
    if innings_num == 2:
        prev_inn = db.query(models.Innings).filter_by(match_id=mid, innings_number=1).first()
        innings.target = prev_inn.total_runs + 1
    db.add(innings); db.flush()

    # Create batting score entries for openers
    batsmen = [data.striker_id]
    if data.non_striker_id:
        batsmen.append(data.non_striker_id)
    for pos, pid in enumerate(batsmen):
        bs = models.BattingScore(
            innings_id=innings.id, player_id=pid,
            batting_position=pos + 1,
            is_on_strike=(pos == 0), is_at_crease=True
        )
        db.add(bs)
    # Create bowling score for first bowler
    bwl = models.BowlingScore(
        innings_id=innings.id, player_id=data.bowler_id, is_current_bowler=True
    )
    db.add(bwl)
    m.current_innings = innings_num
    m.status = "live"
    db.commit(); db.refresh(innings)
    return innings

@app.post("/api/innings/{iid}/ball", response_model=schemas.LiveState)
def record_ball(iid: int, data: schemas.BallRecord, db: Session = Depends(get_db)):
    innings = db.get(models.Innings, iid)
    if not innings: raise HTTPException(404)
    match = db.get(models.Match, innings.match_id)

    is_wide = data.extras_type == "wide"
    is_no_ball = data.extras_type == "no_ball"
    is_legal = not is_wide and not is_no_ball

    # Determine ball/over numbers
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

    # Update innings totals
    innings.total_runs += total_runs
    if data.extras_type in ("wide", "no_ball", "bye", "leg_bye"):
        innings.total_extras += data.extras_runs
    if is_legal:
        innings.total_balls += 1
    if data.is_wicket:
        innings.total_wickets += 1

    # Update batting score for striker
    bat_score = db.query(models.BattingScore).filter_by(
        innings_id=iid, player_id=data.striker_id
    ).first()
    if not bat_score:
        pos = db.query(models.BattingScore).filter_by(innings_id=iid).count() + 1
        bat_score = models.BattingScore(
            innings_id=iid, player_id=data.striker_id,
            batting_position=pos, is_on_strike=True, is_at_crease=True
        )
        db.add(bat_score); db.flush()
    if not is_wide:
        bat_score.balls_faced += 1
        bat_score.runs += data.runs_scored
        if data.runs_scored == 4: bat_score.fours += 1
        if data.runs_scored == 6: bat_score.sixes += 1

    # Handle wicket
    if data.is_wicket and data.dismissed_player_id:
        dismissed = db.query(models.BattingScore).filter_by(
            innings_id=iid, player_id=data.dismissed_player_id
        ).first()
        if dismissed:
            dismissed.is_out = True
            dismissed.is_at_crease = False
            dismissed.is_on_strike = False
            # Build dismissal text
            wtype = data.wicket_type or "out"
            fielder = db.get(models.Player, data.fielder_id) if data.fielder_id else None
            bowler = db.get(models.Player, data.bowler_id)
            if wtype == "caught":
                dismissed.dismissal_text = f"c {fielder.name if fielder else '?'} b {bowler.name}"
            elif wtype == "bowled":
                dismissed.dismissal_text = f"b {bowler.name}"
            elif wtype == "lbw":
                dismissed.dismissal_text = f"lbw b {bowler.name}"
            elif wtype == "run_out":
                dismissed.dismissal_text = f"run out ({fielder.name if fielder else '?'})"
            elif wtype == "stumped":
                dismissed.dismissal_text = f"st {fielder.name if fielder else '?'} b {bowler.name}"
            elif wtype == "hit_wicket":
                dismissed.dismissal_text = f"hit wicket b {bowler.name}"
            else:
                dismissed.dismissal_text = wtype

    # Update bowling score
    bwl_score = db.query(models.BowlingScore).filter_by(
        innings_id=iid, player_id=data.bowler_id
    ).first()
    if not bwl_score:
        bwl_score = models.BowlingScore(
            innings_id=iid, player_id=data.bowler_id, is_current_bowler=True
        )
        db.add(bwl_score); db.flush()
    bwl_score.runs_conceded += data.runs_scored + (data.extras_runs if data.extras_type in ("wide","no_ball") else 0)
    if is_legal:
        bwl_score.balls_bowled += 1
    if is_wide:
        bwl_score.wides += 1
    if is_no_ball:
        bwl_score.no_balls += 1
    if data.is_wicket and data.wicket_type not in ("run_out",):
        bwl_score.wickets += 1

    # Rotate strike on odd runs (and not wide)
    rotate = (data.runs_scored % 2 == 1) and not is_wide
    # End of over: rotate strike
    new_legal = innings.total_balls
    end_of_over = is_legal and (new_legal % 6 == 0)
    if end_of_over:
        rotate = not rotate  # flip because over ended

    if rotate:
        # Swap striker and non-striker in batting scores
        striker_bs = db.query(models.BattingScore).filter_by(innings_id=iid, player_id=data.striker_id).first()
        non_striker_id = data.non_striker_id
        if not non_striker_id:
            # Try to find the other batsman at crease if not provided
            other = db.query(models.BattingScore).filter(
                models.BattingScore.innings_id == iid,
                models.BattingScore.is_at_crease == True,
                models.BattingScore.player_id != data.striker_id
            ).first()
            if other:
                non_striker_id = other.player_id

        if non_striker_id:
            non_striker_bs = db.query(models.BattingScore).filter_by(innings_id=iid, player_id=non_striker_id).first()
            if striker_bs and non_striker_bs:
                striker_bs.is_on_strike = False
                non_striker_bs.is_on_strike = True

    # Ensure at least one person is on strike if anyone is at the crease
    at_crease = db.query(models.BattingScore).filter_by(innings_id=iid, is_at_crease=True).all()
    if len(at_crease) == 1:
        at_crease[0].is_on_strike = True
    elif len(at_crease) > 1:
        on_strike = [b for b in at_crease if b.is_on_strike]
        if not on_strike:
            at_crease[0].is_on_strike = True

    # Check innings complete
    max_wickets = match.players_per_team if match.last_man_stands else match.players_per_team - 1
    max_balls = match.overs * 6
    innings_over = innings.total_wickets >= max_wickets or (is_legal and innings.total_balls >= max_balls)
    if innings_over:
        innings.is_completed = True
        if innings.innings_number == 1:
            match.status = "innings_break"
        else:
            _finish_match(match, innings, db)

    # Check chase complete
    if innings.innings_number == 2 and innings.target and innings.total_runs >= innings.target:
        innings.is_completed = True
        _finish_match(match, innings, db)

    db.commit()
    return _build_live_state(match, innings, db)


@app.post("/api/innings/{iid}/undo", response_model=schemas.LiveState)
def undo_ball(iid: int, db: Session = Depends(get_db)):
    innings = db.get(models.Innings, iid)
    if not innings: raise HTTPException(404)
    match = db.get(models.Match, innings.match_id)

    last_event = db.query(models.BallEvent).filter_by(innings_id=iid).order_by(models.BallEvent.id.desc()).first()
    if not last_event:
        raise HTTPException(400, "No balls to undo in this innings")

    is_wide = last_event.extras_type == "wide"
    is_no_ball = last_event.extras_type == "no_ball"
    is_legal = last_event.is_legal

    # Reverse Innings totals
    innings.total_runs -= last_event.total_runs
    if last_event.extras_type in ("wide", "no_ball", "bye", "leg_bye"):
        innings.total_extras -= last_event.extras_runs
    if is_legal:
        innings.total_balls -= 1
    if last_event.is_wicket:
        innings.total_wickets -= 1

    # Restore Match status
    if innings.is_completed:
        innings.is_completed = False
        match.status = "live"
        match.winner_id = None
        match.result_summary = None

    # Restore Batting state
    crease_batsmen = db.query(models.BattingScore).filter_by(innings_id=iid, is_at_crease=True).all()
    for b in crease_batsmen:
        if b.player_id not in (last_event.striker_id, last_event.non_striker_id):
            if b.balls_faced == 0 and b.runs == 0:
                db.delete(b)
            else:
                b.is_at_crease = False
                b.is_on_strike = False

    striker_bs = db.query(models.BattingScore).filter_by(innings_id=iid, player_id=last_event.striker_id).first()
    if striker_bs:
        striker_bs.is_at_crease = True
        striker_bs.is_on_strike = True
        if not is_wide:
            striker_bs.balls_faced -= 1
            striker_bs.runs -= last_event.runs_scored
            if last_event.runs_scored == 4: striker_bs.fours -= 1
            if last_event.runs_scored == 6: striker_bs.sixes -= 1
        if last_event.is_wicket and last_event.dismissed_player_id == striker_bs.player_id:
            striker_bs.is_out = False
            striker_bs.dismissal_text = None

    non_striker_bs = db.query(models.BattingScore).filter_by(innings_id=iid, player_id=last_event.non_striker_id).first()
    if non_striker_bs:
        non_striker_bs.is_at_crease = True
        non_striker_bs.is_on_strike = False
        if last_event.is_wicket and last_event.dismissed_player_id == non_striker_bs.player_id:
            non_striker_bs.is_out = False
            non_striker_bs.dismissal_text = None

    # Restore Bowling state
    db.query(models.BowlingScore).filter_by(innings_id=iid).update({"is_current_bowler": False})
    bwl_score = db.query(models.BowlingScore).filter_by(innings_id=iid, player_id=last_event.bowler_id).first()
    if bwl_score:
        bwl_score.is_current_bowler = True
        bwl_score.runs_conceded -= last_event.runs_scored + (last_event.extras_runs if last_event.extras_type in ("wide", "no_ball") else 0)
        if is_legal:
            bwl_score.balls_bowled -= 1
        if is_wide:
            bwl_score.wides -= 1
        if is_no_ball:
            bwl_score.no_balls -= 1
        if last_event.is_wicket and last_event.wicket_type not in ("run_out",):
            bwl_score.wickets -= 1

    db.delete(last_event)
    db.commit()

    return _build_live_state(match, innings, db)


def _finish_match(match, innings, db):
    if innings.innings_number == 2:
        inn1 = db.query(models.Innings).filter_by(match_id=match.id, innings_number=1).first()
        if innings.total_runs >= innings.target:
            # chasing team won
            match.winner_id = innings.batting_team_id
            total_possible_wkts = match.players_per_team if match.last_man_stands else match.players_per_team - 1
            wkts_left = total_possible_wkts - innings.total_wickets
            match.result_summary = f"{innings.batting_team.name} won by {wkts_left} wickets"
        else:
            runs_diff = inn1.total_runs - innings.total_runs
            match.winner_id = inn1.batting_team_id
            match.result_summary = f"{inn1.batting_team.name} won by {runs_diff} runs"
    match.status = "completed"


def _build_live_state(match, innings, db) -> schemas.LiveState:
    bat_scores = db.query(models.BattingScore).filter_by(innings_id=innings.id).all()
    bwl_scores = db.query(models.BowlingScore).filter_by(innings_id=innings.id).all()
    all_events = db.query(models.BallEvent).filter_by(innings_id=innings.id).all()

    over_num = innings.total_balls // 6
    cur_over_events = [e for e in all_events if e.over_number == over_num]

    # Recent 3 overs summary
    recent_overs = []
    for o in range(max(0, over_num - 2), over_num):
        evts = [e for e in all_events if e.over_number == o]
        total = sum(e.total_runs for e in evts)
        wkts = sum(1 for e in evts if e.is_wicket)
        recent_overs.append({"over": o + 1, "runs": total, "wickets": wkts,
                              "balls": [_ball_display(e) for e in evts]})

    overs_f = innings.total_balls / 6
    run_rate = round(innings.total_runs / overs_f, 2) if overs_f > 0 else 0.0
    req_rate = None
    if innings.innings_number == 2 and innings.target:
        rem_runs = innings.target - innings.total_runs
        rem_balls = match.overs * 6 - innings.total_balls
        req_rate = round(rem_runs / (rem_balls / 6), 2) if rem_balls > 0 else None

    def bat_out(b):
        p = db.get(models.Player, b.player_id)
        return schemas.BattingScoreOut(
            id=b.id, player_id=b.player_id,
            player_name=p.name if p else "",
            runs=b.runs, balls_faced=b.balls_faced,
            fours=b.fours, sixes=b.sixes,
            strike_rate=b.strike_rate,
            is_out=b.is_out, dismissal_text=b.dismissal_text,
            batting_position=b.batting_position,
            is_on_strike=b.is_on_strike, is_at_crease=b.is_at_crease
        )

    def bwl_out(b):
        p = db.get(models.Player, b.player_id)
        return schemas.BowlingScoreOut(
            id=b.id, player_id=b.player_id,
            player_name=p.name if p else "",
            balls_bowled=b.balls_bowled, overs_display=b.overs_display,
            maidens=b.maidens, runs_conceded=b.runs_conceded,
            wickets=b.wickets, wides=b.wides, no_balls=b.no_balls,
            economy_rate=b.economy_rate, is_current_bowler=b.is_current_bowler
        )

    last = all_events[-1] if all_events else None
    return schemas.LiveState(
        match=schemas.MatchOut.model_validate(match),
        innings=schemas.InningsOut.model_validate(innings),
        batting_scores=[bat_out(b) for b in bat_scores],
        bowling_scores=[bwl_out(b) for b in bwl_scores],
        current_over_events=[schemas.BallEventOut.model_validate(e) for e in cur_over_events],
        recent_overs=recent_overs,
        run_rate=run_rate,
        required_rate=req_rate,
        last_event=schemas.BallEventOut.model_validate(last) if last else None
    )


def _ball_display(event):
    if event.is_wicket:
        return "W"
    if event.extras_type == "wide":
        return f"Wd+{event.extras_runs}"
    if event.extras_type == "no_ball":
        return f"Nb+{event.runs_scored}"
    if event.extras_type in ("bye", "leg_bye"):
        return f"{event.extras_type[0].upper()}+{event.extras_runs}"
    return str(event.runs_scored)


@app.get("/api/innings/{iid}/live", response_model=schemas.LiveState)
def get_live(iid: int, db: Session = Depends(get_db)):
    innings = db.get(models.Innings, iid)
    if not innings: raise HTTPException(404)
    match = db.get(models.Match, innings.match_id)
    return _build_live_state(match, innings, db)


@app.get("/api/matches/{mid}/live", response_model=schemas.LiveState)
def get_match_live(mid: int, db: Session = Depends(get_db)):
    match = db.get(models.Match, mid)
    if not match: raise HTTPException(404)
    innings = db.query(models.Innings).filter_by(
        match_id=mid, innings_number=match.current_innings
    ).first()
    if not innings: raise HTTPException(404, "No innings started yet")
    return _build_live_state(match, innings, db)


@app.get("/api/matches/{mid}/scorecard", response_model=schemas.FullScorecard)
def get_scorecard(mid: int, db: Session = Depends(get_db)):
    match = db.get(models.Match, mid)
    if not match: raise HTTPException(404)
    all_innings = db.query(models.Innings).filter_by(match_id=mid).order_by(models.Innings.innings_number).all()
    innings_list = []
    for inn in all_innings:
        bat_scores = db.query(models.BattingScore).filter_by(innings_id=inn.id).order_by(models.BattingScore.batting_position).all()
        bwl_scores = db.query(models.BowlingScore).filter_by(innings_id=inn.id).all()
        def bat_out(b):
            p = db.get(models.Player, b.player_id)
            return schemas.BattingScoreOut(
                id=b.id, player_id=b.player_id, player_name=p.name if p else "",
                runs=b.runs, balls_faced=b.balls_faced, fours=b.fours, sixes=b.sixes,
                strike_rate=b.strike_rate, is_out=b.is_out, dismissal_text=b.dismissal_text,
                batting_position=b.batting_position, is_on_strike=b.is_on_strike, is_at_crease=b.is_at_crease
            )
        def bwl_out(b):
            p = db.get(models.Player, b.player_id)
            return schemas.BowlingScoreOut(
                id=b.id, player_id=b.player_id, player_name=p.name if p else "",
                balls_bowled=b.balls_bowled, overs_display=b.overs_display,
                maidens=b.maidens, runs_conceded=b.runs_conceded, wickets=b.wickets,
                wides=b.wides, no_balls=b.no_balls, economy_rate=b.economy_rate,
                is_current_bowler=b.is_current_bowler
            )
        overs_f = inn.total_balls // 6
        rem = inn.total_balls % 6
        overs_display = f"{overs_f}.{rem}"
        innings_list.append(schemas.ScorecardInnings(
            innings=schemas.InningsOut.model_validate(inn),
            batting_team=schemas.TeamBrief.model_validate(inn.batting_team),
            bowling_team=schemas.TeamBrief.model_validate(inn.bowling_team),
            batting_scores=[bat_out(b) for b in bat_scores],
            bowling_scores=[bwl_out(b) for b in bwl_scores],
            fall_of_wickets=[],
            overs_display=overs_display
        ))
    return schemas.FullScorecard(
        match=schemas.MatchOut.model_validate(match),
        innings_list=innings_list
    )


@app.post("/api/innings/{iid}/next-bowler")
def set_next_bowler(iid: int, bowler_id: int, db: Session = Depends(get_db)):
    db.query(models.BowlingScore).filter_by(innings_id=iid).update({"is_current_bowler": False})
    bwl = db.query(models.BowlingScore).filter_by(innings_id=iid, player_id=bowler_id).first()
    if not bwl:
        innings = db.get(models.Innings, iid)
        bwl = models.BowlingScore(innings_id=iid, player_id=bowler_id, is_current_bowler=True)
        db.add(bwl)
    else:
        bwl.is_current_bowler = True
    db.commit()
    return {"ok": True}


@app.post("/api/innings/{iid}/next-batsman")
def set_next_batsman(iid: int, player_id: int, on_strike: bool = True, db: Session = Depends(get_db)):
    innings = db.get(models.Innings, iid)
    pos = db.query(models.BattingScore).filter_by(innings_id=iid).count() + 1
    bs = models.BattingScore(
        innings_id=iid, player_id=player_id, batting_position=pos,
        is_on_strike=on_strike, is_at_crease=True
    )
    db.add(bs); db.commit()
    return {"ok": True}


@app.get("/api/tournaments/{tid}/standings")
def get_standings(tid: int, db: Session = Depends(get_db)):
    tournament = db.get(models.Tournament, tid)
    if not tournament: raise HTTPException(404)
    teams = {t.id: {"id": t.id, "name": t.name, "played": 0, "won": 0, "lost": 0, "tied": 0,
                     "nrr": 0.0, "points": 0} for t in tournament.teams}
    for m in tournament.matches:
        if m.status != "completed": continue
        if m.team1_id in teams: teams[m.team1_id]["played"] += 1
        if m.team2_id in teams: teams[m.team2_id]["played"] += 1
        if m.winner_id:
            loser_id = m.team2_id if m.winner_id == m.team1_id else m.team1_id
            if m.winner_id in teams:
                teams[m.winner_id]["won"] += 1
                teams[m.winner_id]["points"] += 2
            if loser_id in teams:
                teams[loser_id]["lost"] += 1
    return sorted(teams.values(), key=lambda x: (-x["points"], -x["won"]))
