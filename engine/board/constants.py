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

WK = 1  # White kingside
WQ = 2  # White queenside
BK = 4  # Black kingside
BQ = 8  # Black queenside


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

A1 = 56
B1 = 57
C1 = 58
D1 = 59
E1 = 60
F1 = 61
G1 = 62
H1 = 63

A8 = 0
B8 = 1
C8 = 2
D8 = 3
E8 = 4
F8 = 5
G8 = 6
H8 = 7

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