from typing import List, Tuple, override
from Piece import Piece

class King(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
        self.name = "King"
        self.symbol = "K"

    @override
    def get_valid_moves(self, board) -> List[Tuple[int, int]]:
        row, col = self.position
        valid_moves = []
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                        (0, 1), (1, -1), (1, 0), (1, 1)]

        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            # check borders
            if board.is_on_board(new_row, new_col):
                current_square = board.get_square(new_row, new_col)
                # check square
                if not current_square.has_team_piece(self.color):
                    valid_moves.append((new_row, new_col))

        # --- (castling) ---
        if not self.has_moved:
            if self._can_castle(board, kingside=True):
                valid_moves.append((row, col+2))
            if self._can_castle(board, kingside=False):
                valid_moves.append((row, col-2))

        return valid_moves

    def _can_castle(self, board, kingside: bool):
        row, col = self.position
        rook_col = 7 if kingside else 0
        step = 1 if kingside else -1
        rook = board.get_piece(row, rook_col)

        # check if rook exist
        if not rook or rook.name != "Rook" or rook.has_moved:
            return False

        # check if there is a free pass between the king and rook
        current_col = col + step
        while current_col != rook_col:
            if not board.get_square(row, current_col).is_empty:
                return False
            current_col += step

        return True

