from abc import ABC, abstractmethod

class Piece(ABC):
    def __init__(self, color: str, position: tuple):
        """
        :param color: 'white' or 'black'
        :param position: tuple (row, col)
        """
        self.color = color
        self.position = position
        self.name = None
        self.symbol = None
        self.has_moved = False

    def set_position(self, new_position: tuple):
        self.position = new_position

    def _get_sliding_moves(self, board, directions):
        valid_moves = []
        row, col = self.position # piece position
        # 1. checking all possible moves
        for dr, dc in directions:
            for i in range(1, 8):
                new_row = row + (dr * i)
                new_col = col + (dc * i)
                # check borders
                if not board.is_on_board(new_row, new_col):
                    break

                target_square = board.get_square(new_row, new_col)
                # check square info
                if target_square.is_empty:
                    valid_moves.append((new_row, new_col))
                else:
                    # has a piece
                    if target_square.has_enemy_piece(self.color):
                        valid_moves.append((new_row, new_col))
                    break
        return valid_moves


    def __str__(self):
        # upper case for white and lower case for black
        if self.color == "white":
            return self.symbol.upper()
        else:
            return self.symbol.lower()

    # --- Abstract Methods  ---
    @abstractmethod
    # returns list of all the valid moves for a piece
    def get_valid_moves(self, board):
        pass

