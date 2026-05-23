# engine/board/utils.py

from engine.board.constants import FILES


def square_to_index(square: str) -> int:
    """
    Converts:
    e4 -> index
    """

    file = FILES.index(square[0])

    rank = 8 - int(square[1])

    return rank * 8 + file


def index_to_square(index: int) -> str:
    """
    Converts:
    index -> e4
    """

    rank = 8 - (index // 8)

    file = index % 8

    return f"{FILES[file]}{rank}"


def is_on_board(rank: int, file: int) -> bool:
    return 0 <= rank < 8 and 0 <= file < 8