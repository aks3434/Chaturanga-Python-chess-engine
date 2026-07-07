from pydantic import BaseModel, Field
from typing import Optional, Literal


class NewGameRequest(BaseModel):
    # "white" / "black" = which side the human plays
    human_color: Literal["white", "black"] = "white"
    # optional starting position; defaults to standard start
    fen: Optional[str] = None
    # engine strength controls -- all optional, all clamped server-side
    skill_level: Optional[int] = Field(default=None, ge=0, le=20)
    think_time_ms: Optional[int] = Field(default=1000, ge=50, le=15000)
    depth: Optional[int] = Field(default=None, ge=1, le=40)


class NewGameResponse(BaseModel):
    game_id: str
    fen: str
    human_color: str
    engine_move: Optional[str] = None  # if engine plays first (human is black)


class MoveRequest(BaseModel):
    # move in UCI notation, e.g. "e2e4", "e7e8q" for promotion
    move: str


class MoveResponse(BaseModel):
    fen: str
    human_move: str
    engine_move: Optional[str] = None
    is_game_over: bool
    result: Optional[str] = None  # "1-0", "0-1", "1/2-1/2"
    reason: Optional[str] = None  # "checkmate", "stalemate", "draw", etc.


class GameStateResponse(BaseModel):
    game_id: str
    fen: str
    pgn: str
    is_game_over: bool
    result: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
