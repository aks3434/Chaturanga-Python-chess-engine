# engine/tests/perft.py

from engine.movegen.generator import MoveGenerator


def perft(board, depth):

    if depth == 0:
        return 1

    generator = MoveGenerator(board)

    moves = generator.generate_moves()

    nodes = 0

    for move in moves:

        board.make_move(move)

        nodes += perft(board, depth - 1)

        board.undo_move(move)

    return nodes