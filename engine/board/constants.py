# engine/board/constants.py

WHITE = 0
BLACK = 1

BOTH = 2

EMPTY = 0

PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6


PIECE_NAMES = {
    PAWN: "P",
    KNIGHT: "N",
    BISHOP: "B",
    ROOK: "R",
    QUEEN: "Q",
    KING: "K"
}


UNICODE_PIECES = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",

    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
}

PROMOTION_PIECES = [
    QUEEN,
    ROOK,
    BISHOP,
    KNIGHT
]

FILES = "abcdefgh"
RANKS = "12345678"


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

TEST_FEN = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"