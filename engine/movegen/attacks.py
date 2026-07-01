# engine/movegen/attacks.py

from engine.board.constants import *
from engine.board.pieces import get_piece_type, get_piece_color

def is_square_attacked(board, square, attacker_color) -> bool:
    """
    Returns True if 'square' is attacked by any piece of 'attacker_color'.
    This is used for check detection and move validation.
    """
    if square is None:
        return False # Safety against missing kings

    rank = square // 8
    file = square % 8

    # Steps for different pieces
    # 1. Pawns
    pawn_rank_dir = 1 if attacker_color == WHITE else -1 # Pawns attack "backwards" from target perspective
    for df in [-1, 1]:
        ar, af = rank + pawn_rank_dir, file + df
        if 0 <= ar < 8 and 0 <= af < 8:
            p = board.get_piece(ar * 8 + af)
            if p != EMPTY and get_piece_type(p) == PAWN and get_piece_color(p) == attacker_color:
                return True

    # 2. Knights
    for dr, df in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
        ar, af = rank + dr, file + df
        if 0 <= ar < 8 and 0 <= af < 8:
            p = board.get_piece(ar * 8 + af)
            if p != EMPTY and get_piece_type(p) == KNIGHT and get_piece_color(p) == attacker_color:
                return True

    # 3. Sliding Pieces (Rook, Bishop, Queen)
    # Vectors: (dr, df)
    # Straight for Rooks/Queens
    straight = [(0,1), (0,-1), (1,0), (-1,0)]
    # Diagonal for Bishops/Queens
    diag = [(1,1), (1,-1), (-1,1), (-1,-1)]

    # Check Straight
    for dr, df in straight:
        for dist in range(1, 8):
            ar, af = rank + dr * dist, file + df * dist
            if 0 <= ar < 8 and 0 <= af < 8:
                p = board.get_piece(ar * 8 + af)
                if p != EMPTY:
                    if get_piece_color(p) == attacker_color:
                        pt = get_piece_type(p)
                        if pt == ROOK or pt == QUEEN: return True
                    break # Blocked
            else: break

    # Check Diagonal
    for dr, df in diag:
        for dist in range(1, 8):
            ar, af = rank + dr * dist, file + df * dist
            if 0 <= ar < 8 and 0 <= af < 8:
                p = board.get_piece(ar * 8 + af)
                if p != EMPTY:
                    if get_piece_color(p) == attacker_color:
                        pt = get_piece_type(p)
                        if pt == BISHOP or pt == QUEEN: return True
                    break # Blocked
            else: break

    # 4. King
    for dr in [-1, 0, 1]:
        for df in [-1, 0, 1]:
            if dr == 0 and df == 0: continue
            ar, af = rank + dr, file + df
            if 0 <= ar < 8 and 0 <= af < 8:
                p = board.get_piece(ar * 8 + af)
                if p != EMPTY and get_piece_type(p) == KING and get_piece_color(p) == attacker_color:
                    return True

    return False