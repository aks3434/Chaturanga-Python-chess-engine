# engine/board/pieces.py

from engine.board.constants import *


def make_piece(piece_type: int, color: int) -> int:
    return piece_type if color == WHITE else -piece_type


def get_piece_type(piece: int) -> int:
    return abs(piece)


def get_piece_color(piece: int):
    if piece > 0:
        return WHITE
    elif piece < 0:
        return BLACK
    return None


def piece_to_char(piece: int) -> str:
    if piece == EMPTY:
        return "."

    piece_type = get_piece_type(piece)
    char = PIECE_NAMES[piece_type]

    return char if piece > 0 else char.lower()