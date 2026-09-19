import Piece

class Square:
    def __init__(self, row, col, piece = None):
        self.row = row
        self.col = col
        self.piece = piece

    @property
    def is_empty(self):
        return self.piece is None

    def has_enemy_piece(self, color: str):
        return (not self.is_empty) and (self.piece.color != color)

    def has_team_piece(self, color):
        return (not self.is_empty) and (self.piece.color == color)

    def set_piece(self, piece):
        self.piece = piece
        if piece:
            piece.set_position((self.row, self.col))

    def remove_piece(self):
        popped_piece = self.piece
        self.piece = None
        return popped_piece

