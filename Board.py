from Square import Square
from Rook import Rook
from Knight import Knight
from Bishop import Bishop
from Queen import Queen
from King import King
from Pawn import Pawn

class Board:
    def __init__(self):
        self.grid = [[Square(row, col) for col in range(8)] for row in range(8)]
        self._prepare_board()

    def _prepare_board(self):
        # --- place pieces ---
        # place pawns
        for col in range(8):
            self.grid[1][col].set_piece(Pawn("black", (1, col)))
            self.grid[6][col].set_piece(Pawn("white", (6, col)))

        # place rocks, knighta, bishops, queens, kings
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col in range(8):
            PeiceClass = piece_order[col]
            self.grid[0][col].set_piece(PeiceClass("black", (0, col)))
            self.grid[7][col].set_piece(PeiceClass("white", (7, col)))

    # --- (Utility Methods) ---

    def is_on_board(self, row, col):
        # check Index Out of Bounds
        return (0 <= row < 8 and 0 <= col < 8)
    
    def get_square(self, row, col):
        # return square obgect 
        if self.is_on_board(row, col):
            return self.grid[row][col]
        return None

    def get_piece(self, row, col):
        square = self.get_square(row, col)
        if square:
            return (square.piece)
        return None

    def __str__(self):
        board_str = ""
        board_str += "   0   1   2   3   4   5   6   7\n"
        board_str += "  ---------------------------------\n"

        for i, row in enumerate(self.grid):
            # add row number 
            row_str = f"{i} | " + " | ".join([str(sq.piece) if sq.piece else " " for sq in row]) + " |"
            board_str += row_str + "\n"

        board_str += "  ---------------------------------\n"
        return board_str

