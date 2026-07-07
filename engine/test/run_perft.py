from engine.board.board import Board
from engine.board.constants import START_FEN
from engine.test.perft import perft


PERFT_TESTS = [
    ("Start position", START_FEN, {1: 20, 2: 400, 3: 8902, 4: 197281}),
    (
        "Kiwipete",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        {1: 48, 2: 2039, 3: 97862, 4: 4085603},
    ),
    (
        "Promotion",
        "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
        {1: 24, 2: 496, 3: 9483},
    ),
    (
        "En passant",
        "1k6/8/8/5pP1/4K1P1/8/8/8 w - f6 0 1",
        {1: 10, 2: 63, 3: 533},
    ),
]


def run_perft_tests():
    passed = 0
    failed = 0

    for name, fen, depths in PERFT_TESTS:
        board = Board()
        board.load_fen(fen)

        for depth, expected in depths.items():
            result = perft(board, depth)

            if result == expected:
                print(f"PASS  {name} depth {depth}: {result}")
                passed += 1
            else:
                print(f"FAIL  {name} depth {depth}: got {result}, expected {expected}")
                failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_perft_tests()
    raise SystemExit(0 if success else 1)
