from typing import List, Tuple, override
from Piece import Piece

class Pawn(Piece):
    def __init__(self, color: str, position: tuple):
        super().__init__(color, position)
        self.name = "Pawn"
        self.symbol = "P"

    @override
    def get_valid_moves(self, board) -> List[Tuple[int, int]]:
        row, col = self.position
        valid_moves = []
        # move and attack direction depends on piece color
        if self.color == "white":
            direction = -1
            starting_row = 6
            attack_directions = [(-1,1),(-1,-1)]
        else:
            direction = 1
            starting_row = 1
            attack_directions = [(1, 1), (1, -1)]

        one_step_row = row + direction

        if board.is_on_board(one_step_row, col):
            square_1 = board.get_square(one_step_row, col)
            if square_1.is_empty:
                valid_moves.append((one_step_row, col))

            # if first step is clear + in start position: can do double step
            if row == starting_row:
                two_step_row = row + 2 * direction
                if board.is_on_board(two_step_row, col):
                    square_2 = board.get_square(two_step_row, col)
                    if square_2.is_empty:
                        valid_moves.append((two_step_row, col))

        # attack conditions
        for dr, dc in attack_directions:
            new_row = dr + row
            new_col = dc + col
            if board.is_on_board(new_row,new_col):
                current_square = board.get_square(new_row, new_col)
                if current_square.has_enemy_piece(self.color):
                    valid_moves.append((new_row,new_col))
                # --- (en passant) ---
                elif hasattr(board, 'en_passant_target') and board.en_passant_target == (new_row, new_col):
                    valid_moves.append((new_row, new_col))

        return valid_moves


