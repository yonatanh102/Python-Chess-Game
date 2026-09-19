from typing import override, List, Tuple
from Piece import Piece

class Queen(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
        self.name = "Queen"
        self.symbol = "Q"

    @override
    def get_valid_moves(self, board) -> List[Tuple[int, int]]:
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        return self._get_sliding_moves(board, directions)