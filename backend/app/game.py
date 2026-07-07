import os
import time
import uuid
import chess

from .engine_manager import EngineSession

MAX_CONCURRENT_GAMES = int(os.environ.get("MAX_CONCURRENT_GAMES", "50"))
GAME_IDLE_TIMEOUT_SECONDS = int(os.environ.get("GAME_IDLE_TIMEOUT_SECONDS", "600"))


class GameSession:
    def __init__(
        self,
        human_color: str,
        fen: str | None = None,
        think_time_ms: int | None = 1000,
        depth: int | None = None,
    ):
        self.game_id = str(uuid.uuid4())
        self.board = chess.Board(fen) if fen else chess.Board()
        self.human_color = human_color  # "white" or "black"
        self.think_time_ms = think_time_ms
        self.depth = depth
        self.engine_session = EngineSession()
        self.last_activity = time.time()

    def touch(self):
        self.last_activity = time.time()

    def is_idle(self) -> bool:
        return (time.time() - self.last_activity) > GAME_IDLE_TIMEOUT_SECONDS

    def engine_to_move(self) -> bool:
        board_turn_is_white = self.board.turn == chess.WHITE
        human_is_white = self.human_color == "white"
        return board_turn_is_white != human_is_white

    def result_info(self):
        if not self.board.is_game_over():
            return False, None, None
        result = self.board.result()
        outcome = self.board.outcome()
        reason = outcome.termination.name.lower() if outcome else None
        return True, result, reason


class GameRegistry:
    """In-memory store of active games.

    Fine for a single-process deployment. If you scale to multiple workers
    you'll want to move this to Redis (or pin sessions to a single worker
    with sticky routing) since engine subprocesses live in process memory.
    """

    def __init__(self):
        self._games: dict[str, GameSession] = {}

    def count(self) -> int:
        return len(self._games)

    def can_create(self) -> bool:
        return self.count() < MAX_CONCURRENT_GAMES

    def add(self, session: GameSession):
        self._games[session.game_id] = session

    def get(self, game_id: str) -> GameSession | None:
        return self._games.get(game_id)

    def remove(self, game_id: str):
        self._games.pop(game_id, None)

    def all_sessions(self):
        return list(self._games.values())


registry = GameRegistry()
