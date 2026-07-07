import chess
import chess.pgn
from fastapi import APIRouter, HTTPException

from ..models import (
    NewGameRequest,
    NewGameResponse,
    MoveRequest,
    MoveResponse,
    GameStateResponse,
)
from ..game import GameSession, registry

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=NewGameResponse)
async def create_game(req: NewGameRequest):
    if not registry.can_create():
        raise HTTPException(
            status_code=503, detail="Server is at max concurrent games, try again shortly."
        )

    try:
        session = GameSession(
            human_color=req.human_color,
            fen=req.fen,
            think_time_ms=req.think_time_ms,
            depth=req.depth,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid FEN.")

    await session.engine_session.start(skill_level=req.skill_level)
    registry.add(session)

    engine_move_uci = None
    # If the human plays black, engine moves first.
    if session.engine_to_move():
        move = await session.engine_session.best_move(
            session.board, think_time_ms=session.think_time_ms, depth=session.depth
        )
        session.board.push(move)
        engine_move_uci = move.uci()

    session.touch()
    return NewGameResponse(
        game_id=session.game_id,
        fen=session.board.fen(),
        human_color=session.human_color,
        engine_move=engine_move_uci,
    )


@router.post("/{game_id}/move", response_model=MoveResponse)
async def make_move(game_id: str, req: MoveRequest):
    session = registry.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found.")

    try:
        move = chess.Move.from_uci(req.move)
    except ValueError:
        raise HTTPException(status_code=400, detail="Malformed move string.")

    if move not in session.board.legal_moves:
        raise HTTPException(status_code=400, detail="Illegal move.")

    session.board.push(move)
    session.touch()

    is_over, result, reason = session.result_info()
    engine_move_uci = None

    if not is_over and session.engine_to_move():
        engine_move = await session.engine_session.best_move(
            session.board, think_time_ms=session.think_time_ms, depth=session.depth
        )
        session.board.push(engine_move)
        engine_move_uci = engine_move.uci()
        is_over, result, reason = session.result_info()

    return MoveResponse(
        fen=session.board.fen(),
        human_move=req.move,
        engine_move=engine_move_uci,
        is_game_over=is_over,
        result=result,
        reason=reason,
    )


@router.get("/{game_id}", response_model=GameStateResponse)
async def get_game(game_id: str):
    session = registry.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found.")

    is_over, result, _ = session.result_info()
    pgn_game = chess.pgn.Game.from_board(session.board)

    return GameStateResponse(
        game_id=session.game_id,
        fen=session.board.fen(),
        pgn=str(pgn_game),
        is_game_over=is_over,
        result=result,
    )


@router.delete("/{game_id}")
async def end_game(game_id: str):
    session = registry.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found.")
    await session.engine_session.stop()
    registry.remove(game_id)
    return {"detail": "Game ended."}
