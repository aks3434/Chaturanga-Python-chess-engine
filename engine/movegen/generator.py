# engine/movegen/generator.py

from engine.board.constants import *
from engine.board.pieces import *
from engine.board.move import Move
from engine.board.utils import is_on_board

from engine.movegen.directions import *
from engine.movegen.attacks import is_square_attacked

class MoveGenerator:

    def __init__(self, board):
        self.board = board

    def generate_moves(self):

        moves = []

        for square in range(64):

            piece = self.board.get_piece(square)

            if piece == EMPTY:
                continue

            color = get_piece_color(piece)

            if color != self.board.side_to_move:
                continue

            piece_type = get_piece_type(piece)

            if piece_type == PAWN:
                self.generate_pawn_moves(square, piece, moves)

            elif piece_type == KNIGHT:
                self.generate_knight_moves(square, piece, moves)

            elif piece_type == BISHOP:
                self.generate_sliding_moves(
                    square,
                    piece,
                    moves,
                    BISHOP_DIRECTIONS
                    )

            elif piece_type == ROOK:
                self.generate_sliding_moves(
                    square,
                    piece,
                    moves,
                    ROOK_DIRECTIONS
                 )

            elif piece_type == QUEEN:
                self.generate_sliding_moves(
                    square,
                    piece,
                    moves,
                    QUEEN_DIRECTIONS
                )

            elif piece_type == KING:
                self.generate_king_moves(square, piece, moves)


        return self.filter_legal_moves(moves)
    
    def generate_pawn_moves(self, square, piece, moves):

        rank = square // 8
        file = square % 8

        color = get_piece_color(piece)

        direction = -1 if color == WHITE else 1

        start_rank = 6 if color == WHITE else 1

        # Single push
        new_rank = rank + direction

        if is_on_board(new_rank, file):

            target_square = new_rank * 8 + file
            promotion_rank = 0 if color ==WHITE else 7

            if self.board.is_empty(target_square):

                if new_rank == promotion_rank:
                    for promotion_piece in PROMOTION_PIECES:
                        moves.append(
                            Move(
                                square,
                                target_square,
                                piece,
                                promotion=promotion_piece
                            )
                        )

                else:
                    moves.append(Move(square , target_square , piece))


                # Double push
                if rank == start_rank:

                    double_rank = rank + (2 * direction)

                    double_square = double_rank * 8 + file

                    if self.board.is_empty(double_square):

                        moves.append(
                            Move(square, double_square, piece)
                        )

            # Captures
            for df in [-1, 1]:

                new_file = file + df

                if is_on_board(new_rank, new_file):

                    target_square = new_rank * 8 + new_file

                    target_piece = self.board.get_piece(target_square)

                    if (
                        target_piece != EMPTY and
                        get_piece_color(target_piece) != color
                    ):

                        if new_rank == promotion_rank:
                            for promotion_piece in PROMOTION_PIECES:
                                moves.append(
                                    Move(
                                        square,
                                        target_square,
                                        piece,
                                        captured=target_piece,
                                        promotion=promotion_piece
                                    )
                                )
                        else:
                            moves.append(
                                Move(
                                    square,
                                    target_square,
                                    piece,
                                    captured=target_piece
                                )
                            )
                        
            for df in [-1,1]:
                new_file = file + df
                if is_on_board(new_rank , new_file):
                    target_square = new_rank*8 + new_file
        
                    if target_square == self.board.en_passant:
                        captured_square = (
                            target_square + 8
                            if color == WHITE
                            else target_square - 8

                        )
                        
                        captured_piece = self.board.get_piece(captured_square)

                        moves.append(
                            Move(
                                square,
                                target_square,
                                piece,
                                captured=captured_piece,
                                is_en_passant=True
                            )
                        )
                        
    def generate_knight_moves(self, square, piece, moves):

        rank = square // 8
        file = square % 8

        color = get_piece_color(piece)

        for dr, df in KNIGHT_DIRECTIONS:

            new_rank = rank + dr
            new_file = file + df

            if not is_on_board(new_rank, new_file):
                continue

            target_square = new_rank * 8 + new_file

            target_piece = self.board.get_piece(target_square)

            # Empty square
            if target_piece == EMPTY:

                moves.append(
                    Move(square, target_square, piece)
                )

            # Capture
            elif get_piece_color(target_piece) != color:

                moves.append(
                    Move(
                        square,
                        target_square,
                        piece,
                        captured=target_piece
                    )
                )
    
    def generate_sliding_moves(
        self,
        square,
        piece,
        moves,
        directions
        ):

        rank = square // 8
        file = square % 8

        color = get_piece_color(piece)

        for dr, df in directions:

            new_rank = rank + dr
            new_file = file + df

            while is_on_board(new_rank, new_file):

                target_square = new_rank * 8 + new_file

                target_piece = self.board.get_piece(target_square)

                # Empty square
                if target_piece == EMPTY:

                    moves.append(
                        Move(square, target_square, piece)
                    )

                else:

                    # Enemy capture
                    if get_piece_color(target_piece) != color:

                        moves.append(
                            Move(
                                square,
                                target_square,
                                piece,
                                captured=target_piece
                            )
                        )

                    # Stop sliding after collision
                    break

                new_rank += dr
                new_file += df

    def generate_king_moves(self, square, piece, moves):

        rank = square // 8
        file = square % 8

        color = get_piece_color(piece)

        # Normal King Moves
        for dr, df in KING_DIRECTIONS:

            new_rank = rank + dr
            new_file = file + df

            if not is_on_board(new_rank, new_file):
                continue

            target_square = new_rank * 8 + new_file
            target_piece = self.board.get_piece(target_square)

            if target_piece == EMPTY:

                moves.append(
                Move(square, target_square, piece)
                )

            elif get_piece_color(target_piece) != color:

                moves.append(
                    Move(
                    square,
                    target_square,
                    piece,
                    captured=target_piece
                )
                )

        # =========================
        # CASTLING MOVES
        # =========================

        # WHITE CASTLING
        if color == WHITE and square == E1:

            # White Kingside
            if self.board.castling_rights & WK:

                if (
                    self.board.get_piece(F1) == EMPTY and
                    self.board.get_piece(G1) == EMPTY
                ):

                    if (
                        not is_square_attacked(self.board, E1, BLACK) and
                        not is_square_attacked(self.board, F1, BLACK) and
                        not is_square_attacked(self.board, G1, BLACK)
                    ):

                        rook = self.board.get_piece(H1)

                        if (
                            rook != EMPTY and
                            get_piece_type(rook) == ROOK and
                            get_piece_color(rook) == WHITE
                        ):

                            moves.append(
                                Move(
                                    E1,
                                    G1,
                                    piece,
                                    is_castling=True
                                )
                            )

            # White Queenside
            if self.board.castling_rights & WQ:

                if (
                    self.board.get_piece(B1) == EMPTY and
                    self.board.get_piece(C1) == EMPTY and
                    self.board.get_piece(D1) == EMPTY
                ):

                    if (
                        not is_square_attacked(self.board, E1, BLACK) and
                        not is_square_attacked(self.board, D1, BLACK) and
                        not is_square_attacked(self.board, C1, BLACK)
                    ):

                        rook = self.board.get_piece(A1)

                        if (
                            rook != EMPTY and
                            get_piece_type(rook) == ROOK and
                            get_piece_color(rook) == WHITE
                        ):

                            moves.append(
                                Move(
                                    E1,
                                    C1,
                                    piece,
                                    is_castling=True
                                )
                            )

        # BLACK CASTLING
        elif color == BLACK and square ==E8:

            # Black Kingside
            if self.board.castling_rights & BK:

                if (
                    self.board.get_piece(F8) == EMPTY and
                    self.board.get_piece(G8) == EMPTY
                ):

                    if (
                        not is_square_attacked(self.board,E8, WHITE) and
                        not is_square_attacked(self.board,F8, WHITE) and
                        not is_square_attacked(self.board,G8, WHITE)
                    ):

                        rook = self.board.get_piece(H8)

                        if (
                            rook != EMPTY and
                            get_piece_type(rook) == ROOK and
                            get_piece_color(rook) == BLACK
                        ):

                            moves.append(
                                Move(
                                    E8,
                                    G8,
                                    piece,
                                    is_castling=True
                                )
                            )

            # Black Queenside
            if self.board.castling_rights & BQ:

                if (
                    self.board.get_piece(B8) == EMPTY and
                    self.board.get_piece(C8) == EMPTY and
                    self.board.get_piece(D8) == EMPTY
                ):

                    if (
                        not is_square_attacked(self.board,E8, WHITE) and
                        not is_square_attacked(self.board,D8, WHITE) and
                        not is_square_attacked(self.board,C8, WHITE)
                    ):

                        rook = self.board.get_piece(A8)

                        if (
                            rook != EMPTY and
                            get_piece_type(rook) == ROOK and
                            get_piece_color(rook) == BLACK
                            ):

                            moves.append(
                                Move(
                                    E8,
                                    C8,
                                piece,
                                is_castling=True
                                )
                        )
    def filter_legal_moves(self, moves):

        legal_moves = []

        color = self.board.side_to_move

        opponent = BLACK if color == WHITE else WHITE

        for move in moves:

            self.board.make_move(move)

            king_square = self.board.find_king(color)

            in_check = is_square_attacked(
                self.board,
                king_square,
                opponent
            )

            self.board.undo_move(move)

            if not in_check:
                legal_moves.append(move)

        return legal_moves