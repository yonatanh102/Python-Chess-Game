from typing import List, Tuple, override
from Piece import Piece

class Knight(Piece):
    def __init__(self, color: str, position: tuple):
        super().__init__(color, position)
        self.name = "Knight"
        self.symbol = "N"

    @override
    def get_valid_moves(self, board) -> List[Tuple[int, int]]:
        valid_moves = []
        row, col = self.position
        directions = [(-2, -1),(-2, 1),(-1, -2),(-1, 2),
                        (1, -2),(1, 2),(2, -1),(2, 1)]

        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            #  check borders
            if board.is_on_board(new_row, new_col):
                current_square = board.get_square(new_row, new_col)
                # check square
                if not current_square.has_team_piece(self.color):
                    valid_moves.append((new_row, new_col))

        return valid_moves