# engine/board/zobrist.py

import random
from engine.board.constants import WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING

# Seed for reproducibility
_rng = random.Random(20240101)

def _rand64():
    return _rng.getrandbits(64)

# PIECE_KEYS[color][piece_type][square]
PIECE_KEYS = [
    [[_rand64() for _ in range(64)] for _ in range(7)],   # WHITE 
    [[_rand64() for _ in range(64)] for _ in range(7)],   # BLACK
]

# One key per possible en-passant file (0–7)
EP_KEYS = [_rand64() for _ in range(8)]

# One key per castling-rights bitmask value (0–15)
CASTLE_KEYS = [_rand64() for _ in range(16)]

# Flip side-to-move
SIDE_KEY = _rand64()

def compute_hash(board) -> int:
    """Compute Zobrist hash from scratch."""
    from engine.board.pieces import get_piece_type, get_piece_color
    from engine.board.constants import EMPTY

    h = 0
    for square in range(64):
        piece = board.squares[square]
        if piece == EMPTY: continue
        pt = get_piece_type(piece)
        c  = get_piece_color(piece)
        h ^= PIECE_KEYS[c][pt][square]

    if board.en_passant is not None:
        h ^= EP_KEYS[board.en_passant % 8]

    h ^= CASTLE_KEYS[board.castling_rights]

    if board.side_to_move == BLACK:
        h ^= SIDE_KEY

    return h
