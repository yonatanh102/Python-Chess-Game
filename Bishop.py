from typing import List, Tuple, override
from Piece import Piece

class Bishop(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
        self.name = "Bishop"
        self.symbol = "B"

    @override
    def get_valid_moves(self, board) -> List[Tuple[int, int]]:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self._get_sliding_moves(board, directions)