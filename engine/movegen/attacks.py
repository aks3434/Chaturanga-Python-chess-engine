# engine/movegen/attacks.py

from engine.board.constants import *
from engine.board.pieces import *

from engine.movegen.directions import *

from engine.board.utils import is_on_board


def is_square_attacked(board, square, attacker_color):

    rank = square // 8
    file = square % 8

    # =========================
    # Pawn attacks
    # =========================

    pawn_direction = 1 if attacker_color == WHITE else -1

    for df in [-1, 1]:

        new_rank = rank + pawn_direction
        new_file = file + df

        if is_on_board(new_rank, new_file):

            target_square = new_rank * 8 + new_file

            piece = board.get_piece(target_square)

            if piece != EMPTY:

                if (
                    get_piece_type(piece) == PAWN and
                    get_piece_color(piece) == attacker_color
                ):
                    return True

    # =========================
    # Knight attacks
    # =========================

    for dr, df in KNIGHT_DIRECTIONS:

        new_rank = rank + dr
        new_file = file + df

        if is_on_board(new_rank, new_file):

            target_square = new_rank * 8 + new_file

            piece = board.get_piece(target_square)

            if piece != EMPTY:

                if (
                    get_piece_type(piece) == KNIGHT and
                    get_piece_color(piece) == attacker_color
                ):
                    return True

    # =========================
    # Sliding attacks
    # =========================

    sliding_pieces = [
        (BISHOP_DIRECTIONS, [BISHOP, QUEEN]),
        (ROOK_DIRECTIONS, [ROOK, QUEEN])
    ]

    for directions, attackers in sliding_pieces:

        for dr, df in directions:

            new_rank = rank + dr
            new_file = file + df

            while is_on_board(new_rank, new_file):

                target_square = new_rank * 8 + new_file

                piece = board.get_piece(target_square)

                if piece != EMPTY:

                    if (
                        get_piece_color(piece) == attacker_color and
                        get_piece_type(piece) in attackers
                    ):
                        return True

                    break

                new_rank += dr
                new_file += df

    # =========================
    # King attacks
    # =========================

    for dr, df in KING_DIRECTIONS:

        new_rank = rank + dr
        new_file = file + df

        if is_on_board(new_rank, new_file):

            target_square = new_rank * 8 + new_file

            piece = board.get_piece(target_square)

            if piece != EMPTY:

                if (
                    get_piece_type(piece) == KING and
                    get_piece_color(piece) == attacker_color
                ):
                    return True

    return False