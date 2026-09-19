import pytest
import sys
import os

# Add the root directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Board import Board
from King import King
from Rook import Rook
from Bishop import Bishop
from Queen import Queen
from Game import Game
from Square import Square

def create_empty_board():
    """ 
    Helper function: Creates a completely empty board for isolated testing 
    without standard chess piece interference.
    """
    board = Board()
    board.grid = [[Square(row, col) for col in range(8)] for row in range(8)]
    return board

def test_king_basic_moves_and_capture():
    """ Verify basic 8-directional movement and capturing an enemy piece. """
    board = create_empty_board()
    
    king = King("white", (4, 4))
    enemy_queen = Queen("black", (3, 4))
    
    board.grid[4][4].set_piece(king)
    board.grid[3][4].set_piece(enemy_queen)
    
    valid_moves = king.get_valid_moves(board)
    
    # The King should have 8 possible moves, including capturing the enemy at (3, 4)
    expected_moves = [
        (3, 3), (3, 4), (3, 5),
        (4, 3),         (4, 5),
        (5, 3), (5, 4), (5, 5)
    ]
    
    assert len(valid_moves) == 8
    for move in expected_moves:
        assert move in valid_moves

def test_king_cannot_move_into_check():
    """ Verify that the king is restricted from moving onto attacked squares. """
    game = Game()
    game.board = create_empty_board()
    
    king = King("white", (7, 4))
    enemy_rook = Rook("black", (6, 0)) # Controls the entire 6th rank
    
    game.board.get_square(7, 4).set_piece(king)
    game.board.get_square(6, 0).set_piece(enemy_rook)
    game.init_bitboards()
    
    legal_moves = game.get_legal_moves(king)
    
    # Safe moves on the 7th rank
    assert (7, 3) in legal_moves
    assert (7, 5) in legal_moves
    # Illegal moves on the 6th rank (controlled by enemy rook)
    assert (6, 3) not in legal_moves
    assert (6, 4) not in legal_moves
    assert (6, 5) not in legal_moves

def test_must_resolve_check():
    """ Verify that pieces can only make moves that resolve an active check. """
    game = Game()
    game.board = create_empty_board()
    game.turn = "white"
    
    white_king = King("white", (7, 4))
    white_rook = Rook("white", (0, 0)) 
    enemy_rook = Rook("black", (0, 4)) # Attacking the king
    
    game.board.get_square(7, 4).set_piece(white_king)
    game.board.get_square(0, 0).set_piece(white_rook)
    game.board.get_square(0, 4).set_piece(enemy_rook)
    game.init_bitboards()
    
    rook_legal_moves = game.get_legal_moves(white_rook)
    
    # Moving elsewhere ignores the check and should be illegal
    assert (1, 0) not in rook_legal_moves
    assert (2, 0) not in rook_legal_moves
    
    # Capturing the checking piece resolves the threat and is legal
    assert (0, 4) in rook_legal_moves

def test_checkmate():
    """ Verify the game correctly identifies a checkmate scenario. """
    game = Game()
    game.board = create_empty_board()
    game.turn = "white"
    
    # Setup classic back-rank checkmate
    white_king = King("white", (7, 4))
    enemy_rook1 = Rook("black", (7, 0)) # Delivers the check
    enemy_rook2 = Rook("black", (6, 0)) # Cuts off escape squares
    
    game.board.get_square(7, 4).set_piece(white_king)
    game.board.get_square(7, 0).set_piece(enemy_rook1)
    game.board.get_square(6, 0).set_piece(enemy_rook2)
    game.init_bitboards()
    
    status = game.check_game_over()
    
    assert status is not None
    assert "Checkmate" in status
    assert "Black wins" in status

def test_castling():
    """ Verify valid kingside castling shifts both King and Rook correctly. """
    game = Game()
    game.board = create_empty_board()
    
    king = King("white", (7, 4))
    rook = Rook("white", (7, 7))
    
    game.board.get_square(7, 4).set_piece(king)
    game.board.get_square(7, 7).set_piece(rook)
    game.init_bitboards()
    
    legal_moves = game.get_legal_moves(king)
    assert (7, 6) in legal_moves
    
    # Execute castling
    game.make_move((7, 4), (7, 6))
    
    # Validate new positions
    assert not game.board.get_square(7, 6).is_empty
    assert game.board.get_piece(7, 6).name == "King"
    assert not game.board.get_square(7, 5).is_empty
    assert game.board.get_piece(7, 5).name == "Rook"

def test_castling_blocked_and_has_moved():
    """ Verify castling is blocked by intermediate pieces or prior movement. """
    game = Game()
    game.board = create_empty_board()
    
    king = King("white", (7, 4))
    rook_right = Rook("white", (7, 7))
    blocker = Bishop("white", (7, 5)) 
    
    game.board.get_square(7, 4).set_piece(king)
    game.board.get_square(7, 7).set_piece(rook_right)
    game.board.get_square(7, 5).set_piece(blocker)
    game.init_bitboards()
    
    # Blocked by Bishop
    legal_moves = game.get_legal_moves(king)
    assert (7, 6) not in legal_moves 
    
    # Remove blocker, but mark king as moved
    game.board.get_square(7, 5).remove_piece()
    game.init_bitboards()
    king.has_moved = True
    
    legal_moves_after = game.get_legal_moves(king)
    assert (7, 6) not in legal_moves_after

def test_castling_through_check():
    """ Verify castling is illegal if the king passes through an attacked square. """
    game = Game()
    game.board = create_empty_board()
    
    king = King("white", (7, 4))
    rook = Rook("white", (7, 7))
    enemy_rook = Rook("black", (0, 5)) # Attacks the f1 (7, 5) transit square
    
    game.board.get_square(7, 4).set_piece(king)
    game.board.get_square(7, 7).set_piece(rook)
    game.board.get_square(0, 5).set_piece(enemy_rook)
    game.init_bitboards()
    
    legal_moves = game.get_legal_moves(king)
    assert (7, 6) not in legal_moves

def test_stalemate():
    """ Verify the game correctly identifies a stalemate scenario. """
    game = Game()
    game.board = create_empty_board()
    game.turn = "white"
    
    white_king = King("white", (7, 7))
    black_queen = Queen("black", (5, 6)) # Traps king without checking
    
    game.board.get_square(7, 7).set_piece(white_king)
    game.board.get_square(5, 6).set_piece(black_queen)
    game.init_bitboards()
    
    status = game.check_game_over()
    assert status is not None
    assert "Stalemate" in status

def test_pinned_piece_cannot_move():
    """ Verify that pieces pinned to the king cannot step out of the pin line. """
    game = Game()
    game.board = create_empty_board()
    
    king = King("white", (7, 4))
    pinned_rook = Rook("white", (6, 4))
    enemy_rook = Rook("black", (0, 4))
    
    game.board.get_square(7, 4).set_piece(king)
    game.board.get_square(6, 4).set_piece(pinned_rook)
    game.board.get_square(0, 4).set_piece(enemy_rook)
    game.init_bitboards()
    
    legal_moves = game.get_legal_moves(pinned_rook)
    # Moving sideways exposes the king to check
    assert (6, 3) not in legal_moves