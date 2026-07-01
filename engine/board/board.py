# engine/board/board.py

from engine.board.constants import *
from engine.board.pieces import *
from engine.board.utils import square_to_index, index_to_square
from engine.board.zobrist import compute_hash, PIECE_KEYS, EP_KEYS, CASTLE_KEYS, SIDE_KEY

class Board:
    def __init__(self):
        self.squares = [EMPTY] * 64
        self.side_to_move = WHITE
        self.en_passant = None
        self.castling_rights = 0
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.history = []
        self.hash = 0

    def reset(self):
        self.__init__()

    def print_board(self):
        print()
        for rank in range(8):
            print(8 - rank, end="  ")
            for file in range(8):
                square = rank * 8 + file
                piece = self.squares[square]
                print(piece_to_char(piece), end=" ")
            print()
        print("\n   a b c d e f g h\n")

    def load_fen(self, fen: str):
        self.reset()
        parts = fen.split()
        board_part, side_part, castle_part, ep_part, hmc, fmn = parts

        # Castle rights
        rights = 0
        if 'K' in castle_part: rights |= WK
        if 'Q' in castle_part: rights |= WQ
        if 'k' in castle_part: rights |= BK
        if 'q' in castle_part: rights |= BQ
        self.castling_rights = rights

        # Board squares
        rank, file = 0, 0
        for char in board_part:
            if char == "/":
                rank += 1
                file = 0
                continue
            if char.isdigit():
                file += int(char)
                continue
            square = rank * 8 + file
            color = WHITE if char.isupper() else BLACK
            piece_type = {'p':PAWN,'n':KNIGHT,'b':BISHOP,'r':ROOK,'q':QUEEN,'k':KING}[char.lower()]
            self.squares[square] = make_piece(piece_type, color)
            file += 1

        self.side_to_move = WHITE if side_part == 'w' else BLACK
        self.en_passant = None if ep_part == "-" else square_to_index(ep_part)
        self.halfmove_clock = int(hmc)
        self.fullmove_number = int(fmn)
        
        # Initial hash
        self.hash = compute_hash(self)

    def to_fen(self) -> str:
        fen_parts = []
        
        # 1. Piece placement
        ranks = []
        for rank in range(8):
            empty_count = 0
            rank_chars = []
            for file in range(8):
                sq = rank * 8 + file
                piece = self.squares[sq]
                if piece == EMPTY:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank_chars.append(str(empty_count))
                        empty_count = 0
                    rank_chars.append(piece_to_char(piece))
            if empty_count > 0:
                rank_chars.append(str(empty_count))
            ranks.append("".join(rank_chars))
        fen_parts.append("/".join(ranks))

        # 2. Side to move
        fen_parts.append("w" if self.side_to_move == WHITE else "b")

        # 3. Castling rights
        rights_str = ""
        if self.castling_rights & WK: rights_str += "K"
        if self.castling_rights & WQ: rights_str += "Q"
        if self.castling_rights & BK: rights_str += "k"
        if self.castling_rights & BQ: rights_str += "q"
        fen_parts.append(rights_str if rights_str else "-")

        # 4. En passant
        if self.en_passant is not None:
            fen_parts.append(index_to_square(self.en_passant))
        else:
            fen_parts.append("-")

        # 5. Halfmove clock
        fen_parts.append(str(self.halfmove_clock))

        # 6. Fullmove number
        fen_parts.append(str(self.fullmove_number))

        return " ".join(fen_parts)

    def get_piece(self, square: int) -> int:
        return self.squares[square]

    def set_piece(self, square: int, piece: int):
        self.squares[square] = piece

    def is_empty(self, square: int) -> bool:
        return self.squares[square] == EMPTY

    def make_move(self, move):
        # Save state with hash
        self.history.append((self.castling_rights, self.en_passant, self.halfmove_clock, self.fullmove_number, self.hash))
        
        # 1. XOR out old reversible state
        self.hash ^= CASTLE_KEYS[self.castling_rights]
        if self.en_passant is not None:
            self.hash ^= EP_KEYS[self.en_passant % 8]

        self.en_passant = None
        moving_pc, moving_color, moving_type = move.piece, get_piece_color(move.piece), get_piece_type(move.piece)
        
        # 2. Update piece on hash (from)
        self.hash ^= PIECE_KEYS[moving_color][moving_type][move.from_square]
        
        # 3. Handle capture
        if move.captured:
            self.hash ^= PIECE_KEYS[get_piece_color(move.captured)][get_piece_type(move.captured)][move.to_square]

        # Apply move
        if move.promotion:
            self.squares[move.to_square] = make_piece(move.promotion, moving_color)
        else:
            self.squares[move.to_square] = move.piece
        self.squares[move.from_square] = EMPTY

        # En Passant logic
        if moving_type == PAWN:
            if abs(move.to_square - move.from_square) == 16:
                self.en_passant = (move.from_square + move.to_square) // 2
            elif move.is_en_passant:
                cap_sq = move.to_square + 8 if moving_color == WHITE else move.to_square - 8
                self.hash ^= PIECE_KEYS[1-moving_color][PAWN][cap_sq]
                self.squares[cap_sq] = EMPTY

        # Castling logic
        if move.is_castling:
            if move.to_square == G1: self.squares[H1]=EMPTY; self.squares[F1]=make_piece(ROOK,WHITE); self.hash^=PIECE_KEYS[WHITE][ROOK][H1]^PIECE_KEYS[WHITE][ROOK][F1]
            elif move.to_square == C1: self.squares[A1]=EMPTY; self.squares[D1]=make_piece(ROOK,WHITE); self.hash^=PIECE_KEYS[WHITE][ROOK][A1]^PIECE_KEYS[WHITE][ROOK][D1]
            elif move.to_square == G8: self.squares[H8]=EMPTY; self.squares[F8]=make_piece(ROOK,BLACK); self.hash^=PIECE_KEYS[BLACK][ROOK][H8]^PIECE_KEYS[BLACK][ROOK][F8]
            elif move.to_square == C8: self.squares[A8]=EMPTY; self.squares[D8]=make_piece(ROOK,BLACK); self.hash^=PIECE_KEYS[BLACK][ROOK][A8]^PIECE_KEYS[BLACK][ROOK][D8]

        # Update castling rights
        if moving_type == KING:
            self.castling_rights &= ~(WK|WQ) if moving_color == WHITE else ~(BK|BQ)
        if move.from_square == H1 or move.to_square == H1: self.castling_rights &= ~WK
        if move.from_square == A1 or move.to_square == A1: self.castling_rights &= ~WQ
        if move.from_square == H8 or move.to_square == H8: self.castling_rights &= ~BK
        if move.from_square == A8 or move.to_square == A8: self.castling_rights &= ~BQ

        # 4. XOR in new state
        placed_pc = self.squares[move.to_square]
        self.hash ^= PIECE_KEYS[moving_color][get_piece_type(placed_pc)][move.to_square]
        self.hash ^= CASTLE_KEYS[self.castling_rights]
        if self.en_passant is not None:
            self.hash ^= EP_KEYS[self.en_passant % 8]
        
        self.side_to_move = 1 - self.side_to_move
        self.hash ^= SIDE_KEY

    def undo_move(self, move):
        (self.castling_rights, self.en_passant, self.halfmove_clock, self.fullmove_number, self.hash) = self.history.pop()
        
        moving_color = get_piece_color(move.piece)
        self.squares[move.from_square] = move.piece
        self.squares[move.to_square] = move.captured if not move.is_en_passant else EMPTY

        if move.is_en_passant:
            cap_sq = move.to_square + 8 if moving_color == WHITE else move.to_square - 8
            self.squares[cap_sq] = make_piece(PAWN, 1 - moving_color)
        
        if move.is_castling:
            if move.to_square == G1: self.squares[F1]=EMPTY; self.squares[H1]=make_piece(ROOK,WHITE)
            elif move.to_square == C1: self.squares[D1]=EMPTY; self.squares[A1]=make_piece(ROOK,WHITE)
            elif move.to_square == G8: self.squares[F8]=EMPTY; self.squares[H8]=make_piece(ROOK,BLACK)
            elif move.to_square == C8: self.squares[D8]=EMPTY; self.squares[A8]=make_piece(ROOK,BLACK)
            
        self.side_to_move = 1 - self.side_to_move

    def find_king(self, color):
        target_piece = make_piece(KING, color)
        for sq in range(64):
            if self.squares[sq] == target_piece:
                return sq
        return None
