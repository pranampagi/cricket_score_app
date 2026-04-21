from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from api.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    format = Column(String(50), default="league")  # league, knockout
    overs_per_match = Column(Integer, default=20)
    players_per_team = Column(Integer, default=11)
    status = Column(String(50), default="setup")  # setup, in_progress, completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    teams = relationship("Team", back_populates="tournament", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True)

    tournament = relationship("Tournament", back_populates="teams")
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    role = Column(String(50), default="batsman")  # batsman, bowler, all_rounder, wicket_keeper

    team = relationship("Team", back_populates="players")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True)
    team1_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team2_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    overs = Column(Integer, default=20)
    players_per_team = Column(Integer, default=11)
    toss_winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    toss_decision = Column(String(10), nullable=True)  # bat, bowl
    status = Column(String(50), default="setup")  # setup, toss, live, innings_break, completed
    current_innings = Column(Integer, default=0)  # 0=not started, 1=first, 2=second
    winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tournament = relationship("Tournament", back_populates="matches")
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    toss_winner = relationship("Team", foreign_keys=[toss_winner_id])
    winner = relationship("Team", foreign_keys=[winner_id])
    innings = relationship("Innings", back_populates="match", cascade="all, delete-orphan")


class Innings(Base):
    __tablename__ = "innings"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    batting_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    bowling_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    innings_number = Column(Integer, nullable=False)  # 1 or 2
    total_runs = Column(Integer, default=0)
    total_wickets = Column(Integer, default=0)
    total_balls = Column(Integer, default=0)
    total_extras = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    target = Column(Integer, nullable=True)  # Target for 2nd innings

    match = relationship("Match", back_populates="innings")
    batting_team = relationship("Team", foreign_keys=[batting_team_id])
    bowling_team = relationship("Team", foreign_keys=[bowling_team_id])
    ball_events = relationship("BallEvent", back_populates="innings", cascade="all, delete-orphan")
    batting_scores = relationship("BattingScore", back_populates="innings", cascade="all, delete-orphan")
    bowling_scores = relationship("BowlingScore", back_populates="innings", cascade="all, delete-orphan")


class BallEvent(Base):
    __tablename__ = "ball_events"

    id = Column(Integer, primary_key=True, index=True)
    innings_id = Column(Integer, ForeignKey("innings.id"), nullable=False)
    over_number = Column(Integer, nullable=False)  # 0-indexed
    ball_number = Column(Integer, nullable=False)  # 1-6 for legal deliveries
    striker_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    non_striker_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    bowler_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    runs_scored = Column(Integer, default=0)  # Runs credited to batsman
    extras_type = Column(String(20), nullable=True)  # wide, no_ball, bye, leg_bye
    extras_runs = Column(Integer, default=0)  # Runs from extras
    total_runs = Column(Integer, default=0)  # Total runs from this ball
    is_wicket = Column(Boolean, default=False)
    wicket_type = Column(String(30), nullable=True)
    dismissed_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    fielder_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    is_legal = Column(Boolean, default=True)  # False for wides and no-balls
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    innings = relationship("Innings", back_populates="ball_events")
    striker = relationship("Player", foreign_keys=[striker_id])
    non_striker = relationship("Player", foreign_keys=[non_striker_id])
    bowler = relationship("Player", foreign_keys=[bowler_id])
    dismissed_player = relationship("Player", foreign_keys=[dismissed_player_id])
    fielder = relationship("Player", foreign_keys=[fielder_id])


class BattingScore(Base):
    __tablename__ = "batting_scores"

    id = Column(Integer, primary_key=True, index=True)
    innings_id = Column(Integer, ForeignKey("innings.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    runs = Column(Integer, default=0)
    balls_faced = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    is_out = Column(Boolean, default=False)
    dismissal_text = Column(String(200), nullable=True)
    batting_position = Column(Integer, default=0)
    is_on_strike = Column(Boolean, default=False)
    is_at_crease = Column(Boolean, default=False)

    innings = relationship("Innings", back_populates="batting_scores")
    player = relationship("Player")

    @property
    def strike_rate(self):
        if self.balls_faced == 0:
            return 0.0
        return round((self.runs / self.balls_faced) * 100, 2)


class BowlingScore(Base):
    __tablename__ = "bowling_scores"

    id = Column(Integer, primary_key=True, index=True)
    innings_id = Column(Integer, ForeignKey("innings.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    balls_bowled = Column(Integer, default=0)  # Legal deliveries
    maidens = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    wickets = Column(Integer, default=0)
    wides = Column(Integer, default=0)
    no_balls = Column(Integer, default=0)
    is_current_bowler = Column(Boolean, default=False)

    innings = relationship("Innings", back_populates="bowling_scores")
    player = relationship("Player")

    @property
    def overs_display(self):
        full_overs = self.balls_bowled // 6
        remaining = self.balls_bowled % 6
        return f"{full_overs}.{remaining}"

    @property
    def economy_rate(self):
        if self.balls_bowled == 0:
            return 0.0
        overs = self.balls_bowled / 6
        return round(self.runs_conceded / overs, 2)
