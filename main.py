import sys

def _run_perft():
    from engine.test.run_perft import run_perft_tests
    success = run_perft_tests()
    raise SystemExit(0 if success else 1)

def _run_search_demo():
    from engine.board.board import Board
    from engine.board.constants import START_FEN
    from engine.search.search import find_best_move_iterative

    board = Board()
    board.load_fen(START_FEN)
    board.print_board()

    depth = 6
    print(f"\nSearching to depth {depth} using Iterative Deepening...\n")
    best = find_best_move_iterative(board, depth, verbose=False)
    print(f"\nBEST MOVE: {best}")

def _run_uci():
    from engine.uci.uci import run_uci
    run_uci()

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--perft" in args:
        _run_perft()
    elif "--search" in args:
        _run_search_demo()
    else:
        _run_uci()