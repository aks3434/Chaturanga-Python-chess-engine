# engine/uci/uci.py
"""
UCI (Universal Chess Interface) protocol handler.

Allows Chaturanga to communicate with any UCI-compatible chess GUI
(Arena, Cute Chess, Lichess bot, etc.) or be tested manually via stdin.

Protocol reference: http://wbec-ridderkerk.nl/html/UCIProtocol.html

Usage:
    python main.py          → enters UCI loop (standard mode)
    python main.py --perft  → runs perft correctness tests
"""

import sys

from engine.board.board import Board
from engine.board.constants import START_FEN
from engine.board.move import Move
from engine.board.utils import square_to_index
from engine.board.pieces import get_piece_type, make_piece, get_piece_color
from engine.board.constants import (
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
    WHITE, BLACK,
    PROMOTION_PIECES, PIECE_NAMES
)
from engine.movegen.generator import MoveGenerator
from engine.search.search import find_best_move_iterative

ENGINE_NAME    = "Chaturanga"
ENGINE_AUTHOR  = "Chaturanga Dev"
DEFAULT_DEPTH  = 5


# ---------------------------------------------------------------------------
# Helper: parse a move in long algebraic notation (e.g. "e2e4", "a7a8q")
# ---------------------------------------------------------------------------

def _parse_move(board: Board, move_str: str) -> Move | None:
    """
    Parses a UCI move string and returns the matching legal Move, or None.
    """
    if len(move_str) < 4:
        return None

    from_sq = square_to_index(move_str[0:2])
    to_sq   = square_to_index(move_str[2:4])

    promotion = 0
    if len(move_str) == 5:
        promo_char = move_str[4].lower()
        promo_map  = {'q': QUEEN, 'r': ROOK, 'b': BISHOP, 'n': KNIGHT}
        promotion  = promo_map.get(promo_char, 0)

    generator = MoveGenerator(board)
    legal_moves = generator.generate_moves()

    for move in legal_moves:
        if move.from_square == from_sq and move.to_square == to_sq:
            if promotion:
                if move.promotion == promotion:
                    return move
            else:
                if not move.promotion:
                    return move

    return None


# ---------------------------------------------------------------------------
# Helper: apply a sequence of UCI move strings to the board
# ---------------------------------------------------------------------------

def _apply_moves(board: Board, move_strings: list[str]):
    for ms in move_strings:
        move = _parse_move(board, ms)
        if move is None:
            print(f"info string ERROR: illegal move '{ms}'", flush=True)
            return
        board.make_move(move)


# ---------------------------------------------------------------------------
# UCI command handlers
# ---------------------------------------------------------------------------

def _cmd_uci():
    print(f"id name {ENGINE_NAME}")
    print(f"id author {ENGINE_AUTHOR}")
    print("option name Depth type spin default 5 min 1 max 20")
    print("option name OwnBook type check default true")
    print("option name BookPath type string default book.bin")
    print("uciok", flush=True)


def _cmd_isready():
    print("readyok", flush=True)


def _cmd_position(board: Board, tokens: list[str]):
    """
    Handles:
      position startpos [moves e2e4 ...]
      position fen <fen> [moves ...]
    """
    board.reset()

    if not tokens:
        board.load_fen(START_FEN)
        return

    idx = 0
    if tokens[idx] == "startpos":
        board.load_fen(START_FEN)
        idx += 1
    elif tokens[idx] == "fen":
        idx += 1
        fen_parts = []
        while idx < len(tokens) and tokens[idx] != "moves":
            fen_parts.append(tokens[idx])
            idx += 1
        board.load_fen(" ".join(fen_parts))
    else:
        board.load_fen(START_FEN)

    if idx < len(tokens) and tokens[idx] == "moves":
        idx += 1
        _apply_moves(board, tokens[idx:])


def _cmd_go(board: Board, tokens: list[str], default_depth: int) -> int:
    """
    Handles 'go' command. Supports: wtime, btime, winc, binc, depth
    """
    wtime = btime = None
    winc = binc = 0
    depth = default_depth

    # Parse UCI tokens
    for i, tok in enumerate(tokens):
        if tok == "wtime" and i + 1 < len(tokens): wtime = int(tokens[i+1])
        elif tok == "btime" and i + 1 < len(tokens): btime = int(tokens[i+1])
        elif tok == "winc" and i + 1 < len(tokens): winc = int(tokens[i+1])
        elif tok == "binc" and i + 1 < len(tokens): binc = int(tokens[i+1])
        elif tok == "depth" and i + 1 < len(tokens): depth = int(tokens[i+1])

    # Simple Time Budgeting
    time_limit = None
    my_time = wtime if board.side_to_move == WHITE else btime
    my_inc = winc if board.side_to_move == WHITE else binc
    
    if my_time is not None:
        # Budget: (Time / 40) + half of increment
        time_limit = (my_time / 40.0 + my_inc / 2.0) / 1000.0

    # Call the iterative search
    best = find_best_move_iterative(board, max_depth=depth, time_limit=time_limit)

    if best is None:
        print("bestmove 0000", flush=True)
    else:
        # We use str(best) to explicitly convert the Move object to "e2e4"
        print(f"bestmove {str(best)}", flush=True)

    return depth


# ---------------------------------------------------------------------------
# Main UCI loop
# ---------------------------------------------------------------------------

def run_uci():
    board = Board()
    board.load_fen(START_FEN)
    depth = DEFAULT_DEPTH

    print(f"# {ENGINE_NAME} UCI engine ready. Type 'uci' to begin.", flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        tokens = line.split()
        cmd    = tokens[0]

        if cmd == "uci":
            _cmd_uci()

        elif cmd == "isready":
            _cmd_isready()

        elif cmd == "setoption":
            try:
                name_idx = tokens.index("name")
                if "value" in tokens:
                    val_idx = tokens.index("value")
                    opt_name = " ".join(tokens[name_idx + 1:val_idx]).strip()
                    opt_val = " ".join(tokens[val_idx + 1:]).strip()
                else:
                    opt_name = " ".join(tokens[name_idx + 1:]).strip()
                    opt_val = ""
                
                from engine.search import book
                if opt_name.lower() == "ownbook":
                    book.USE_BOOK = (opt_val.lower() in ("true", "1", "on", "yes"))
                elif opt_name.lower() == "bookpath":
                    book.BOOK_PATH = opt_val
            except ValueError:
                pass

        elif cmd == "ucinewgame":
            board = Board()
            board.load_fen(START_FEN)

        elif cmd == "position":
            _cmd_position(board, tokens[1:])

        elif cmd == "go":
            depth = _cmd_go(board, tokens[1:], depth)

        elif cmd == "stop":
            pass   # future: interrupt iterative deepening

        elif cmd == "quit":
            break

        elif cmd == "d":
            # Non-standard but handy: print the current board
            board.print_board()

        elif cmd == "eval":
            # Non-standard: show static evaluation
            from engine.search.evaluation import evaluate
            score = evaluate(board)
            sign  = "+" if score >= 0 else ""
            print(f"info string eval {sign}{score} cp (from White's perspective)", flush=True)

        elif cmd == "perft":
            # Non-standard shorthand: run a quick perft
            d = int(tokens[1]) if len(tokens) > 1 else 1
            from engine.test.perft import perft
            import time
            t0    = time.perf_counter()
            nodes = perft(board, d)
            dt    = time.perf_counter() - t0
            nps   = int(nodes / dt) if dt > 0 else 0
            print(f"info string perft({d}) = {nodes} nodes  ({dt:.2f}s, {nps:,} nps)", flush=True)

        else:
            print(f"info string unknown command '{cmd}'", flush=True)
