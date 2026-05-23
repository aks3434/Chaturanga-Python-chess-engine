from dataclasses import dataclass

from engine.board.utils import index_to_square
from engine.board.constants import PIECE_NAMES

@dataclass
class Move:

    from_square: int
    to_square: int

    piece: int

    captured: int = 0

    promotion: int = 0

    is_castling: bool = False

    is_en_passant: bool = False

    def __str__(self):

        move_string = (
            f"{index_to_square(self.from_square)}"
            f"{index_to_square(self.to_square)}"
        )

        if self.promotion:
            move_string += PIECE_NAMES[self.promotion].lower()

        return move_string