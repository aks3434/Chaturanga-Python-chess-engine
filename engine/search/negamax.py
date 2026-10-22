# engine/search/negamax.py
import time
from engine.movegen.generator import MoveGenerator
from engine.movegen.attacks import is_square_attacked
from engine.search.evaluation import evaluate
from engine.board.constants import WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, EMPTY
from engine.board.pieces import get_piece_type, get_piece_color
from engine.board.zobrist import SIDE_KEY

# Search control variables for time management
SEARCH_LIMIT_TIME = None
SEARCH_START_TIME = None
SEARCH_STOPPED = False
nodes_searched = 0


INF = 999999
MATE_THRESHOLD = 990000

# Most Valuable Victim – Least Valuable Attacker (MVV-LVA) weights
MVV_LVA_VICTIM = {1: 10, 2: 20, 3: 30, 4: 40, 5: 50, 6: 60}    # piece types
MVV_LVA_ATTACKER = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}

# Transposition Table: hash → (score, depth, flag, best_move)
TT = {}
TT_SIZE = 1 << 20

def clear_tt():
    TT.clear()

# Search Heuristics
MAX_PLY = 64
killers = [[None, None] for _ in range(MAX_PLY)]
history = [[0] * 64 for _ in range(7)]

def clear_killers_and_history():
    for i in range(MAX_PLY):
        killers[i] = [None, None]
    for i in range(7):
        for j in range(64):
            history[i][j] = 0

def value_to_tt(val: int, ply: int) -> int:
    """Adjust checkmate score relative to the current position before storing in TT."""
    if val > MATE_THRESHOLD:
        return val + ply
    if val < -MATE_THRESHOLD:
        return val - ply
    return val

def value_from_tt(val: int, ply: int) -> int:
    """Restore checkmate score relative to the root when retrieving from TT."""
    if val > MATE_THRESHOLD:
        return val - ply
    if val < -MATE_THRESHOLD:
        return val + ply
    return val

def _move_score(move, ply: int = 0, tt_move = None) -> int:
    """Heuristic score for move ordering."""
    if tt_move is not None and move == tt_move:
        return 2_000_000

    if move.captured:
        victim   = MVV_LVA_VICTIM.get(get_piece_type(move.captured), 0)
        attacker = MVV_LVA_ATTACKER.get(get_piece_type(move.piece), 6)
        return 1_000_000 + victim * 10 - attacker
    
    if move.promotion:
        return 900_000

    if ply < MAX_PLY:
        if move == killers[ply][0]: return 800_000
        if move == killers[ply][1]: return 700_000

    return history[get_piece_type(move.piece)][move.to_square]

def _is_in_check(board, color) -> bool:
    king_square = board.find_king(color)
    if king_square is None: return False
    opponent = BLACK if color == WHITE else WHITE
    return is_square_attacked(board, king_square, opponent)

def _has_non_pawn_material(board, color) -> bool:
    """Check if the given color has non-pawn material (crucial to avoid NMP zugzwang)."""
    for sq in range(64):
        p = board.squares[sq]
        if p != EMPTY and get_piece_color(p) == color:
            pt = get_piece_type(p)
            if pt in (KNIGHT, BISHOP, ROOK, QUEEN):
                return True
    return False

def quiescence_search(board, alpha, beta) -> int:

    global nodes_searched, SEARCH_STOPPED
    nodes_searched += 1
    
    # Check limit every 2048 nodes
    if nodes_searched % 2048 == 0:
        if SEARCH_LIMIT_TIME is not None and (time.perf_counter() - SEARCH_START_TIME) >= SEARCH_LIMIT_TIME:
            SEARCH_STOPPED = True
            
    if SEARCH_STOPPED:
        return alpha
        
    in_check = _is_in_check(board, board.side_to_move)

    if not in_check:
        raw = evaluate(board)
        stand_pat = raw if board.side_to_move == WHITE else -raw

        if stand_pat >= beta: return beta
        if stand_pat > alpha: alpha = stand_pat

    generator = MoveGenerator(board)
    all_moves = generator.generate_moves()
    
    if in_check:
        # If in check, we must search all legal moves to escape check
        moves = all_moves
    else:
        # Otherwise, only search captures (and promotions, which are highly tactical)
        moves = [m for m in all_moves if m.captured or m.promotion]

    moves.sort(key=lambda m: _move_score(m, 0), reverse=True)

    if in_check and not moves:
        return -INF  # Checkmate (no moves to escape check)

    for move in moves:
        board.make_move(move)
        score = -quiescence_search(board, -beta, -alpha)
        board.undo_move(move)

        if score >= beta: return beta
        if score > alpha: alpha = score

    return alpha

def negamax(board, depth: int, alpha: int = -INF, beta: int = INF, ply: int = 0) -> int:

    global nodes_searched, SEARCH_STOPPED
    nodes_searched += 1
    
    # Check limit every 2048 nodes
    if nodes_searched % 2048 == 0:
        if SEARCH_LIMIT_TIME is not None and (time.perf_counter() - SEARCH_START_TIME) >= SEARCH_LIMIT_TIME:
            SEARCH_STOPPED = True
            
    if SEARCH_STOPPED:
        return alpha

    original_alpha = alpha
    in_check = _is_in_check(board, board.side_to_move)

    # TT Lookup
    tt_entry = TT.get(board.hash)
    tt_move = None
    if tt_entry is not None:
        if len(tt_entry) == 4:
            tt_score, tt_depth, tt_flag, tt_move = tt_entry
        else:
            tt_score, tt_depth, tt_flag = tt_entry[:3]

        adjusted_score = value_from_tt(tt_score, ply)
        if tt_depth >= depth:
            if tt_flag == 'exact': return adjusted_score
            elif tt_flag == 'lower': alpha = max(alpha, adjusted_score)
            elif tt_flag == 'upper': beta = min(beta, adjusted_score)
            if alpha >= beta: return adjusted_score

    if depth <= 0:
        return quiescence_search(board, alpha, beta)

    # --- 1. Reverse Futility Pruning (RFP) ---
    # If static evaluation is far above beta at depth 1, we can safely prune.
    if depth == 1 and not in_check and ply > 0:
        raw_eval = evaluate(board)
        val = raw_eval if board.side_to_move == WHITE else -raw_eval
        margin = 120  # ~1.2 pawns margin
        if val - margin >= beta:
            return val - margin  # fail-high

    # Null Move Pruning (skip if in check, or if side has only pawns to avoid zugzwang)
    if depth >= 3 and not in_check and ply > 0 and _has_non_pawn_material(board, board.side_to_move):
        board.side_to_move = 1 - board.side_to_move
        board.hash ^= SIDE_KEY
        score = -negamax(board, depth - 1 - 2, -beta, -beta + 1, ply + 1)
        board.side_to_move = 1 - board.side_to_move
        board.hash ^= SIDE_KEY
        if score >= beta: return beta

    generator = MoveGenerator(board)
    moves = generator.generate_moves()

    if not moves:
        if in_check:
            return -INF + (100 + ply)
        return 0

    moves.sort(key=lambda m: _move_score(m, ply, tt_move), reverse=True)

    best_score = -INF
    best_move = None
    moves_searched = 0

    for move in moves:
        board.make_move(move)
        
        is_killer = ply < MAX_PLY and (move == killers[ply][0] or move == killers[ply][1])
        
        # --- 2. Principal Variation Search (PVS) & Late Move Reductions (LMR) ---
        if moves_searched == 0:
            # Search the first move (PV node) with full window
            score = -negamax(board, depth - 1, -beta, -alpha, ply + 1)
        else:
            # Non-PV node: search with a zero (null) window first
            reduction = 0
            if (
                moves_searched >= 4 
                and depth >= 3 
                and not in_check 
                and not move.captured 
                and not move.promotion 
                and not is_killer
                and not _is_in_check(board, board.side_to_move)
            ):
                reduction = 1
                
            # Search with null window and reduction
            score = -negamax(board, depth - 1 - reduction, -alpha - 1, -alpha, ply + 1)
            
            # If the search failed high (exceeded alpha) and was reduced, re-search at full depth
            if score > alpha and reduction > 0:
                score = -negamax(board, depth - 1, -alpha - 1, -alpha, ply + 1)
                
            # If it still exceeds alpha, re-search with full window [alpha, beta]
            if score > alpha and score < beta:
                score = -negamax(board, depth - 1, -beta, -alpha, ply + 1)
            
        board.undo_move(move)
        moves_searched += 1

        if score > best_score:
            best_score = score
            best_move = move
        if score > alpha:
            alpha = score
        if alpha >= beta:
            if not move.captured and not move.promotion and ply < MAX_PLY:
                killers[ply][1] = killers[ply][0]
                killers[ply][0] = move
                history[get_piece_type(move.piece)][move.to_square] += depth * depth
            break

    # TT Store
    if len(TT) < TT_SIZE:
        flag = 'exact'
        if best_score <= original_alpha: flag = 'upper'
        elif best_score >= beta: flag = 'lower'
        
        stored_score = value_to_tt(best_score, ply)
        TT[board.hash] = (stored_score, depth, flag, best_move)

    return best_score
