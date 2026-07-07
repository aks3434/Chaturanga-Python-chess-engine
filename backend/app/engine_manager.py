"""
Wraps python-chess's async UCI engine interface.

Design choice: one engine subprocess per active game (NOT a shared global
process). UCI engines are stateful -- they track the current position via
`position` + `go` commands -- so sharing one process across concurrent users
would cause their moves/searches to collide. This mirrors how cutechess
spawns a fresh process per game.
"""

import asyncio
import os
import shlex
import sys
import chess
import chess.engine

ENGINE_CMD = os.environ.get("ENGINE_CMD", "python3 /absolute/path/to/your_engine.py")
MAX_THINK_TIME_MS = int(os.environ.get("MAX_THINK_TIME_MS", "15000"))


class EngineSession:
    """One UCI engine subprocess bound to one game."""

    def __init__(self):
        self.transport: asyncio.SubprocessTransport | None = None
        self.engine: chess.engine.UciProtocol | None = None

    async def start(self, skill_level: int | None = None):
        # shlex.split is POSIX-oriented and can mangle Windows backslash paths
        cmd_parts = ENGINE_CMD.split() if sys.platform == "win32" else shlex.split(ENGINE_CMD)
        self.transport, self.engine = await chess.engine.popen_uci(cmd_parts)

        # Apply any supported UCI options if your engine exposes them.
        # Wrap in try/except since not every engine implements every option.
        if skill_level is not None:
            try:
                await self.engine.configure({"Skill Level": skill_level})
            except (chess.engine.EngineError, KeyError):
                pass  # engine doesn't support this option -- ignore silently

    async def best_move(
        self,
        board: chess.Board,
        think_time_ms: int | None = None,
        depth: int | None = None,
    ) -> chess.Move:
        if self.engine is None:
            raise RuntimeError("Engine not started")

        # Clamp requested think time so no client can force a runaway search
        think_time_ms = min(think_time_ms or 1000, MAX_THINK_TIME_MS)

        if depth is not None:
            limit = chess.engine.Limit(depth=depth)
        else:
            limit = chess.engine.Limit(time=think_time_ms / 1000)

        result = await self.engine.play(board, limit)
        if result.move is None:
            raise RuntimeError("Engine returned no move (position may be terminal)")
        return result.move

    async def analyse(
        self, board: chess.Board, think_time_ms: int = 1000
    ) -> dict:
        """Return eval info (score, pv, depth) without playing a move."""
        if self.engine is None:
            raise RuntimeError("Engine not started")
        think_time_ms = min(think_time_ms, MAX_THINK_TIME_MS)
        info = await self.engine.analyse(
            board, chess.engine.Limit(time=think_time_ms / 1000)
        )
        score = info.get("score")
        return {
            "depth": info.get("depth"),
            "score_cp": score.white().score(mate_score=100000) if score else None,
            "pv": [m.uci() for m in info.get("pv", [])],
        }

    async def stop(self):
        if self.engine is not None:
            try:
                await self.engine.quit()
            except Exception:
                pass
        self.engine = None
        self.transport = None
