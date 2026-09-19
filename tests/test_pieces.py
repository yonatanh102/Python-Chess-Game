import pytest
import sys
import os

# Add the root directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Board import Board
from Square import Square
from Knight import Knight
from Bishop import Bishop
from Rook import Rook
from Queen import Queen

def create_empty_board():
    """ Helper function: Creates an empty board for isolated testing. """
    board = Board()
    board.grid = [[Square(row, col) for col in range(8)] for row in range(8)]
    return board

def test_knight_moves_and_capture():
    """ Verify Knight's L-shape moves, captures, and friendly blockers. """
    board = create_empty_board()
    knight = Knight("white", (4, 4))
    enemy_piece = Rook("black", (2, 5))
    friendly_piece = Rook("white", (2, 3))
    
    board.grid[4][4].set_piece(knight)
    board.grid[2][5].set_piece(enemy_piece)
    board.grid[2][3].set_piece(friendly_piece)
    
    valid_moves = knight.get_valid_moves(board)
    
    assert len(valid_moves) == 7 # 8 standard moves - 1 friendly blocker
    assert (2, 5) in valid_moves # Valid capture
    assert (2, 3) not in valid_moves # Invalid due to friendly piece
    assert (3, 6) in valid_moves

def test_bishop_moves_blocking_and_capture():
    """ Verify Bishop's diagonal ray-casting respects blockers. """
    board = create_empty_board()
    bishop = Bishop("white", (4, 4))
    enemy_piece = Rook("black", (2, 2))
    friendly_piece = Rook("white", (6, 6))
    
    board.grid[4][4].set_piece(bishop)
    board.grid[2][2].set_piece(enemy_piece)
    board.grid[6][6].set_piece(friendly_piece)
    
    valid_moves = bishop.get_valid_moves(board)
    
    assert (2, 2) in valid_moves # Capture is valid
    assert (1, 1) not in valid_moves # Cannot slide past enemy
    
    assert (5, 5) in valid_moves
    assert (6, 6) not in valid_moves # Friendly blocker
    assert (7, 7) not in valid_moves

def test_rook_moves_and_capture():
    """ Verify Rook's straight ray-casting respects blockers. """
    board = create_empty_board()
    rook = Rook("black", (4, 4))
    enemy_piece = Knight("white", (4, 6))
    
    board.grid[4][4].set_piece(rook)
    board.grid[4][6].set_piece(enemy_piece)
    
    valid_moves = rook.get_valid_moves(board)
    
    assert (4, 5) in valid_moves
    assert (4, 6) in valid_moves # Valid capture
    assert (4, 7) not in valid_moves # Cannot slide past enemy
    
    assert (3, 4) in valid_moves
    assert (0, 4) in valid_moves

def test_queen_moves():
    """ Verify Queen combines both Rook and Bishop mechanics. """
    board = create_empty_board()
    queen = Queen("white", (4, 4))
    
    board.grid[4][4].set_piece(queen)
    valid_moves = queen.get_valid_moves(board)
    
    # 27 total moves on an empty board (14 diagonal + 14 straight - 1 origin square)
    assert len(valid_moves) == 27
    
    assert (0, 0) in valid_moves
    assert (4, 0) in valid_moves
    assert (7, 4) in valid_moves
    assert (1, 7) in valid_moves