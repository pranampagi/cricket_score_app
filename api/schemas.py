from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Tournament ──────────────────────────────────────────────────

class TournamentCreate(BaseModel):
    name: str
    format: str = "league"
    overs_per_match: int = 20
    players_per_team: int = 11


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


class TournamentOut(BaseModel):
    id: int
    name: str
    format: str
    overs_per_match: int
    players_per_team: int
    status: str
    created_at: datetime
    teams: list["TeamOut"] = []
    matches: list["MatchBrief"] = []

    class Config:
        from_attributes = True


# ── Team ────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str
    tournament_id: Optional[int] = None


class TeamOut(BaseModel):
    id: int
    name: str
    tournament_id: Optional[int] = None
    players: list["PlayerOut"] = []

    class Config:
        from_attributes = True


class TeamBrief(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ── Player ──────────────────────────────────────────────────────

class PlayerCreate(BaseModel):
    name: str
    team_id: int
    role: str = "batsman"


class PlayerOut(BaseModel):
    id: int
    name: str
    team_id: int
    role: str

    class Config:
        from_attributes = True


# ── Match ───────────────────────────────────────────────────────

class MatchCreate(BaseModel):
    tournament_id: Optional[int] = None
    team1_id: int
    team2_id: int
    overs: int = 20
    players_per_team: int = 11


class TossRecord(BaseModel):
    toss_winner_id: int
    toss_decision: str  # "bat" or "bowl"


class MatchBrief(BaseModel):
    id: int
    team1_id: int
    team2_id: int
    overs: int
    status: str
    winner_id: Optional[int] = None
    result_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MatchOut(BaseModel):
    id: int
    tournament_id: Optional[int] = None
    team1: TeamBrief
    team2: TeamBrief
    overs: int
    players_per_team: int
    toss_winner_id: Optional[int] = None
    toss_decision: Optional[str] = None
    status: str
    current_innings: int
    winner_id: Optional[int] = None
    result_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Innings ─────────────────────────────────────────────────────

class InningsStart(BaseModel):
    striker_id: int
    non_striker_id: int
    bowler_id: int


class InningsOut(BaseModel):
    id: int
    match_id: int
    batting_team_id: int
    bowling_team_id: int
    innings_number: int
    total_runs: int
    total_wickets: int
    total_balls: int
    total_extras: int
    is_completed: bool
    target: Optional[int] = None

    class Config:
        from_attributes = True


# ── Ball Event ──────────────────────────────────────────────────

class BallRecord(BaseModel):
    striker_id: int
    non_striker_id: int
    bowler_id: int
    runs_scored: int = 0
    extras_type: Optional[str] = None  # wide, no_ball, bye, leg_bye
    extras_runs: int = 0
    is_wicket: bool = False
    wicket_type: Optional[str] = None
    dismissed_player_id: Optional[int] = None
    fielder_id: Optional[int] = None


class BallEventOut(BaseModel):
    id: int
    over_number: int
    ball_number: int
    striker_id: int
    non_striker_id: int
    bowler_id: int
    runs_scored: int
    extras_type: Optional[str] = None
    extras_runs: int
    total_runs: int
    is_wicket: bool
    wicket_type: Optional[str] = None
    dismissed_player_id: Optional[int] = None
    fielder_id: Optional[int] = None
    is_legal: bool

    class Config:
        from_attributes = True


# ── Batting / Bowling Scores ───────────────────────────────────

class BattingScoreOut(BaseModel):
    id: int
    player_id: int
    player_name: str = ""
    runs: int
    balls_faced: int
    fours: int
    sixes: int
    strike_rate: float = 0.0
    is_out: bool
    dismissal_text: Optional[str] = None
    batting_position: int
    is_on_strike: bool
    is_at_crease: bool

    class Config:
        from_attributes = True


class BowlingScoreOut(BaseModel):
    id: int
    player_id: int
    player_name: str = ""
    balls_bowled: int
    overs_display: str = "0.0"
    maidens: int
    runs_conceded: int
    wickets: int
    wides: int
    no_balls: int
    economy_rate: float = 0.0
    is_current_bowler: bool

    class Config:
        from_attributes = True


# ── Live State ──────────────────────────────────────────────────

class LiveState(BaseModel):
    match: MatchOut
    innings: Optional[InningsOut] = None
    batting_scores: list[BattingScoreOut] = []
    bowling_scores: list[BowlingScoreOut] = []
    current_over_events: list[BallEventOut] = []
    recent_overs: list[dict] = []
    run_rate: float = 0.0
    required_rate: Optional[float] = None
    last_event: Optional[BallEventOut] = None


# ── Scorecard ───────────────────────────────────────────────────

class ScorecardInnings(BaseModel):
    innings: InningsOut
    batting_team: TeamBrief
    bowling_team: TeamBrief
    batting_scores: list[BattingScoreOut] = []
    bowling_scores: list[BowlingScoreOut] = []
    fall_of_wickets: list[dict] = []
    overs_display: str = "0.0"


class FullScorecard(BaseModel):
    match: MatchOut
    innings_list: list[ScorecardInnings] = []


# ── Quick Match Setup ──────────────────────────────────────────

class QuickMatchSetup(BaseModel):
    team1_name: str
    team2_name: str
    team1_players: list[str]
    team2_players: list[str]
    overs: int = 20
    players_per_team: int = 11
    toss_winner: int  # 1 or 2
    toss_decision: str  # "bat" or "bowl"
    tournament_id: Optional[int] = None
