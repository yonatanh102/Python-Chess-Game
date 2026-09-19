import pytest
import sys
import os

# Add the root directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Board import Board
from Pawn import Pawn
from Game import Game
from Square import Square
from Rook import Rook

def create_empty_board():
    """ Helper function: Creates an empty board for isolated testing. """
    board = Board()
    board.grid = [[Square(row, col) for col in range(8)] for row in range(8)]
    return board

def test_pawn_initial_two_steps():
    """ Verify a pawn on its starting rank can advance 1 or 2 squares. """
    board = create_empty_board()
    
    pawn = Pawn("white", (6, 4))
    board.grid[6][4].set_piece(pawn)
    
    valid_moves = pawn.get_valid_moves(board)
    assert (5, 4) in valid_moves
    assert (4, 4) in valid_moves

def test_pawn_capture():
    """ Verify pawns capture diagonally but move straight otherwise. """
    board = create_empty_board()
    
    white_pawn = Pawn("white", (4, 4))
    black_pawn1 = Pawn("black", (3, 3))
    black_pawn2 = Pawn("black", (3, 5))
    
    board.grid[4][4].set_piece(white_pawn)
    board.grid[3][3].set_piece(black_pawn1)
    board.grid[3][5].set_piece(black_pawn2)
    
    valid_moves = white_pawn.get_valid_moves(board)
    
    assert (3, 3) in valid_moves
    assert (3, 5) in valid_moves
    assert (3, 4) in valid_moves # Straight path is unblocked

def test_pawn_promotion():
    """ Verify pawns reaching the final rank automatically promote to a Queen. """
    game = Game()
    game.board = create_empty_board()
    
    white_pawn = Pawn("white", (1, 4))
    game.board.get_square(1, 4).set_piece(white_pawn)
    
    game.make_move((1, 4), (0, 4))
    
    promoted_piece = game.board.get_piece(0, 4)
    assert promoted_piece is not None
    assert promoted_piece.name == "Queen"
    assert promoted_piece.color == "white"

def test_en_passant():
    """ Verify full En Passant sequence: target creation, validity, and capture. """
    game = Game()
    game.board = create_empty_board()
    
    white_pawn = Pawn("white", (3, 4))
    black_pawn = Pawn("black", (1, 5))
    
    game.board.get_square(3, 4).set_piece(white_pawn)
    game.board.get_square(1, 5).set_piece(black_pawn)
    
    # Trigger en passant target creation
    game.make_move((1, 5), (3, 5))
    assert game.board.en_passant_target == (2, 5)
    
    # Validate move generation
    valid_moves = white_pawn.get_valid_moves(game.board)
    assert (2, 5) in valid_moves
    
    # Execute capture
    game.make_move((3, 4), (2, 5))
    assert game.board.get_square(3, 5).is_empty # Enemy pawn removed

def test_pawn_blocked_straight():
    """ Verify pawns cannot move or capture straight ahead. """
    game = Game()
    game.board = create_empty_board()
    
    pawn = Pawn("white", (6, 4))
    enemy = Rook("black", (5, 4)) # Block the path
    
    game.board.get_square(6, 4).set_piece(pawn)
    game.board.get_square(5, 4).set_piece(enemy)
    game.init_bitboards()
    
    moves = game.get_legal_moves(pawn)
    assert (5, 4) not in moves
    assert (4, 4) not in moves

def test_en_passant_expires():
    """ Verify the En Passant opportunity expires if not taken immediately. """
    game = Game()
    game.board = create_empty_board()
    
    white_pawn = Pawn("white", (3, 4))
    black_pawn = Pawn("black", (1, 5))
    dummy_piece = Rook("white", (7, 0))
    
    game.board.get_square(3, 4).set_piece(white_pawn)
    game.board.get_square(1, 5).set_piece(black_pawn)
    game.board.get_square(7, 0).set_piece(dummy_piece)
    game.init_bitboards()
    
    # Create target
    game.make_move((1, 5), (3, 5))
    assert game.board.en_passant_target == (2, 5)
    
    # Intervene with another move
    game.make_move((7, 0), (6, 0))
    
    # Ensure opportunity is gone
    valid_moves = game.get_legal_moves(white_pawn)
    assert (2, 5) not in valid_moves