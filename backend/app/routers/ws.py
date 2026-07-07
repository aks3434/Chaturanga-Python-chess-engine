import chess
import chess.engine
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..game import registry

router = APIRouter(tags=["ws"])


@router.websocket("/games/{game_id}/live")
async def game_live(websocket: WebSocket, game_id: str):
    session = registry.get(game_id)
    if session is None:
        await websocket.close(code=4404, reason="Game not found")
        return

    await websocket.accept()
    await websocket.send_json({"type": "state", "fen": session.board.fen()})

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "move":
                await _handle_move(websocket, session, data.get("move", ""))
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json(
                    {"type": "error", "detail": f"Unknown message type: {msg_type}"}
                )
    except WebSocketDisconnect:
        pass  # Client left -- engine subprocess is cleaned up by idle-reaper or DELETE call


async def _handle_move(websocket: WebSocket, session, move_uci: str):
    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        await websocket.send_json({"type": "error", "detail": "Malformed move."})
        return

    if move not in session.board.legal_moves:
        await websocket.send_json({"type": "error", "detail": "Illegal move."})
        return

    session.board.push(move)
    session.touch()
    await websocket.send_json(
        {"type": "human_move", "move": move_uci, "fen": session.board.fen()}
    )

    if session.board.is_game_over():
        await _send_game_over(websocket, session)
        return

    if session.engine_to_move():
        # Use a single search: play() with info streaming to avoid the
        # double-search problem (analysis + best_move were two separate searches).
        think_ms = session.think_time_ms or 1000
        if session.depth is not None:
            limit = chess.engine.Limit(depth=session.depth)
        else:
            limit = chess.engine.Limit(time=think_ms / 1000)

        engine = session.engine_session.engine
        if engine is not None:
            try:
                with await engine.analysis(session.board, limit) as analysis:
                    async for info in analysis:
                        if "score" in info and "depth" in info:
                            score = info["score"].white().score(mate_score=100000)
                            await websocket.send_json(
                                {
                                    "type": "thinking",
                                    "depth": info["depth"],
                                    "score_cp": score,
                                }
                            )
                        # Stop after we get the bestmove (analysis complete)
                        if info.get("string", "").startswith("bestmove") or analysis.would_block():
                            break
            except Exception:
                pass  # engine doesn't support live analysis — fall through to play()

        # Single authoritative search for the actual move
        best = await session.engine_session.best_move(
            session.board, think_time_ms=session.think_time_ms, depth=session.depth
        )
        session.board.push(best)
        await websocket.send_json(
            {"type": "engine_move", "move": best.uci(), "fen": session.board.fen()}
        )

        if session.board.is_game_over():
            await _send_game_over(websocket, session)


async def _send_game_over(websocket: WebSocket, session):
    is_over, result, reason = session.result_info()
    await websocket.send_json(
        {"type": "game_over", "result": result, "reason": reason}
    )
