# engine/search/search.py

import time
from engine.movegen.generator import MoveGenerator
from engine.search.negamax import negamax, _move_score, clear_tt, clear_killers_and_history

INF = 999999

def find_best_move(board, depth: int, alpha: int = -INF, beta: int = INF, verbose: bool = False):
    generator = MoveGenerator(board)
    moves = generator.generate_moves()
    if not moves: return None, -INF

    from engine.search.negamax import TT
    tt_entry = TT.get(board.hash)
    tt_move = tt_entry[3] if tt_entry is not None and len(tt_entry) > 3 else None
    moves.sort(key=lambda m: _move_score(m, 0, tt_move), reverse=True)
    best_move, best_score = None, -INF

    for move in moves:
        board.make_move(move)
        score = -negamax(board, depth - 1, -beta, -alpha, 1)
        board.undo_move(move)
        if score > best_score:
            best_score, best_move = score, move
        if score > alpha: alpha = score
        if alpha >= beta: break

    return best_move, best_score

def find_best_move_iterative(board, max_depth: int = 20, time_limit: float = None, verbose: bool = False):
    # 1. Try opening book move first
    from engine.search.book import get_book_move, find_matching_move
    book_move_str = get_book_move(board)
    if book_move_str:
        best_move = find_matching_move(board, book_move_str)
        if best_move:
            print(f"info string book move: {book_move_str}", flush=True)
            print(f"info depth 1 score cp 0 time 0 pv {best_move}", flush=True)
            return best_move

    clear_tt()
    clear_killers_and_history()
    start_time = time.perf_counter()
    best_move, last_score = None, 0
    
    for depth in range(1, max_depth + 1):
        alpha, beta = -INF, INF
        if depth > 1:
            alpha, beta = last_score - 50, last_score + 50

        move, score = find_best_move(board, depth, alpha, beta, verbose)
        if depth > 1 and (score <= alpha or score >= beta):
            move, score = find_best_move(board, depth, -INF, INF, verbose)

        if move is not None:
            best_move, last_score = move, score

        elapsed = time.perf_counter() - start_time
        print(f"info depth {depth} score cp {last_score} time {int(elapsed * 1000)} pv {best_move}", flush=True)

        if time_limit is not None and (time.perf_counter() - start_time) >= time_limit * 0.5:
            break

    return best_move