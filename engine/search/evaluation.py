# engine/search/evaluation.py

from engine.board.constants import *
from engine.board.pieces import *

PIECE_VALUES = {
    PAWN:   100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK:   500,
    QUEEN:  900,
    KING:   0
}

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_MIDDLEGAME_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

KING_ENDGAME_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]

PST = {
    PAWN:   PAWN_TABLE,
    KNIGHT: KNIGHT_TABLE,
    BISHOP: BISHOP_TABLE,
    ROOK:   ROOK_TABLE,
    QUEEN:  QUEEN_TABLE,
}

def _mirror(square: int) -> int:
    rank, file = divmod(square, 8)
    return (7 - rank) * 8 + file

def evaluate(board) -> int:
    score = 0
    
    # 1. Phase calculation weights:
    # Knight = 1, Bishop = 1, Rook = 2, Queen = 4
    # Max phase weight = 4*1 + 4*1 + 4*2 + 2*4 = 24 (all major pieces on board)
    phase_weight = 0
    for sq in range(64):
        p = board.squares[sq]
        if p == EMPTY: continue
        pt = get_piece_type(p)
        if pt == KNIGHT or pt == BISHOP:
            phase_weight += 1
        elif pt == ROOK:
            phase_weight += 2
        elif pt == QUEEN:
            phase_weight += 4
            
    # Clamp phase weight between 0 and 24
    phase_weight = min(24, max(0, phase_weight))
    # Calculate phase factor: 1.0 = Middlegame, 0.0 = Endgame
    phase = phase_weight / 24.0

    # 2. Positional and Material Evaluation
    for square in range(64):
        piece = board.get_piece(square)
        if piece == EMPTY: continue
        pt, color = get_piece_type(piece), get_piece_color(piece)
        
        val = PIECE_VALUES[pt]
        
        if pt == KING:
            if color == WHITE:
                mg_val = KING_MIDDLEGAME_TABLE[square]
                eg_val = KING_ENDGAME_TABLE[square]
            else:
                mg_val = KING_MIDDLEGAME_TABLE[_mirror(square)]
                eg_val = KING_ENDGAME_TABLE[_mirror(square)]
            pst_val = int((mg_val * phase) + (eg_val * (1.0 - phase)))
        else:
            if color == WHITE:
                pst_val = PST[pt][square]
            else:
                pst_val = PST[pt][_mirror(square)]
                
        if color == WHITE:
            score += val + pst_val
        else:
            score -= (val + pst_val)

    # 3. Tapered King Safety (Safety only matters when board is full of pieces)
    wk, bk = board.find_king(WHITE), board.find_king(BLACK)
    wk_penalty = 0
    bk_penalty = 0
    
    if wk is not None and wk >= 56:
        for f in range(max(0, (wk % 8) - 1), min(8, (wk % 8) + 2)):
            if board.get_piece(48 + f) != make_piece(PAWN, WHITE):
                wk_penalty += 15
                
    if bk is not None and bk <= 7:
        for f in range(max(0, (bk % 8) - 1), min(8, (bk % 8) + 2)):
            if board.get_piece(8 + f) != make_piece(PAWN, BLACK):
                bk_penalty += 15
                
    # Scale penalties by phase (drops to 0 as board empties)
    score -= int(wk_penalty * phase)
    score += int(bk_penalty * phase)

    return score
