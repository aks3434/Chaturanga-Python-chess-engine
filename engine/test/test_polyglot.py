# test_polyglot.py
import struct
from engine.board.board import Board
from engine.board.constants import START_FEN
from engine.search import book

def test():
    # 1. Create a mock book.bin with one entry:
    # Hash for start pos: 0x463b96181691fc9c
    # Move e2e4:
    #   from: e2 (12)
    #   to: e4 (28)
    #   promotion: 0
    #   binary: (12 << 6) | 28 = 768 | 28 = 796
    # Weight: 100
    # Learn: 0
    
    hash_val = 0x463b96181691fc9c
    move_val = 796
    weight_val = 100
    learn_val = 0
    
    entry_bytes = struct.pack(">QHHI", hash_val, move_val, weight_val, learn_val)
    
    book_file = "test_book.bin"
    with open(book_file, "wb") as f:
        f.write(entry_bytes)
        
    print(f"Created mock book '{book_file}' with e2e4 entry.")
    
    # 2. Configure engine to use this book
    book.BOOK_PATH = book_file
    book.USE_BOOK = True
    
    # 3. Load starting position
    board = Board()
    board.load_fen(START_FEN)
    
    # 4. Get book move
    move = book.get_book_move(board)
    print("Move returned from mock book:", move)
    
    # Clean up
    import os
    if os.path.exists(book_file):
        os.remove(book_file)
        
    # Verify
    assert move == "e2e4", f"Expected e2e4, got {move}"
    print("Polyglot book parsing test: SUCCESS!")

if __name__ == "__main__":
    test()
