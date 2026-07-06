# engine/search/book.py

import os
import random

# Global configuration variables modified by UCI commands
USE_BOOK = True
BOOK_PATH = "book.bin"

# Built-in opening book dictionary
# Key: Reduced FEN (first 4 fields: piece placement, side, castling, en passant)
# Value: List of tuples (move_uci, weight)
FALLBACK_BOOK = {
    # Starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -": [("e2e4", 45), ("d2d4", 35), ("g1f3", 10), ("c2c4", 10)],
    # 1. e4 responses
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3": [("c7c5", 45), ("e7e5", 30), ("e7e6", 15), ("c7c6", 10)],
    # 1. d4 responses
    "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3": [("g8f6", 50), ("d7d5", 40), ("e7e6", 10)],
    # Sicilian Defense: 1. e4 c5
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6": [("g1f3", 70), ("b1c3", 20), ("c2c3", 10)],
    # Open Game: 1. e4 e5
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6": [("g1f3", 80), ("b1c3", 10), ("f2f4", 10)],
    # French Defense: 1. e4 e6
    "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": [("d2d4", 85), ("b1c3", 10), ("g1f3", 5)],
    # Caro-Kann Defense: 1. e4 c6
    "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": [("d2d4", 80), ("b1c3", 10), ("g1f3", 10)],
    # Queen's Gambit Prep: 1. d4 d5
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6": [("c2c4", 75), ("g1f3", 15), ("c1f4", 10)],
    # Queen's Gambit: 1. d4 d5 2. c4
    "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq c3": [("e7e6", 50), ("c7c6", 40), ("d5xc4", 10)],
    # Open Game 2. Nf3: 1. e4 e5 2. Nf3
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": [("b8c6", 75), ("g8f6", 15), ("d7d6", 10)],
    # Ruy Lopez/Italian/Scotch Prep: 1. e4 e5 2. Nf3 Nc6
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq -": [("f1b5", 50), ("f1c4", 35), ("d2d4", 15)],
    # Sicilian 2. Nf3: 1. e4 c5 2. Nf3
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": [("d7d6", 40), ("e7e6", 35), ("b8c6", 25)],
    # Indian Game: 1. d4 Nf6
    "rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq -": [("c2c4", 70), ("g1f3", 20), ("c1f4", 10)],
    # Indian Game 2. c4: 1. d4 Nf6 2. c4
    "rnbqkb1r/pppppppp/5n2/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq -": [("e7e6", 50), ("g7g6", 40), ("c7c6", 10)],
}

def get_book_move(board) -> str | None:
    """
    Attempts to read a move from the configured Polyglot opening book.
    Falls back to built-in dictionary if the book file does not exist or
    has no match.
    """
    if not USE_BOOK:
        return None

    fen = board.to_fen()
    
    # 1. Try Polyglot opening book if the file exists
    if os.path.exists(BOOK_PATH):
        try:
            import chess
            import chess.polyglot
            
            chess_board = chess.Board(fen)
            with chess.polyglot.open_reader(BOOK_PATH) as reader:
                entries = list(reader.find_all(chess_board))
                if entries:
                    moves = [entry.move.uci() for entry in entries]
                    weights = [entry.weight for entry in entries]
                    total_weight = sum(weights)
                    if total_weight == 0:
                        return random.choice(moves)
                    else:
                        return random.choices(moves, weights=weights, k=1)[0]
        except Exception as e:
            # Silently fall back to built-in dictionary on error
            pass

    # 2. Fall back to built-in opening book
    # Key is the reduced FEN (first 4 fields)
    reduced_fen = " ".join(fen.split()[:4])
    if reduced_fen in FALLBACK_BOOK:
        candidates = FALLBACK_BOOK[reduced_fen]
        moves = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(moves)
        else:
            return random.choices(moves, weights=weights, k=1)[0]

    return None

def find_matching_move(board, uci_str: str):
    """
    Converts a UCI move string (e.g. 'e2e4') to the engine's internal Move object.
    """
    from engine.movegen.generator import MoveGenerator
    generator = MoveGenerator(board)
    legal_moves = generator.generate_moves()
    for m in legal_moves:
        if str(m) == uci_str:
            return m
    return None
