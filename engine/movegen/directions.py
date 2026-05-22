# engine/movegen/directions.py

KNIGHT_DIRECTIONS = [
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1)
]


KING_DIRECTIONS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1)
]


BISHOP_DIRECTIONS = [
    (-1, -1),
    (-1, 1),
    (1, -1),
    (1, 1)
]


ROOK_DIRECTIONS = [
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1)
]


QUEEN_DIRECTIONS = (
    BISHOP_DIRECTIONS +
    ROOK_DIRECTIONS
)