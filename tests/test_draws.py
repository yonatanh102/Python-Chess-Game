import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Game import Game
from Board import Board
from Square import Square
from King import King
from Knight import Knight
from Rook import Rook

def create_empty_board():
    """ Helper function: Creates an empty board for isolated testing. """
    board = Board()
    board.grid = [[Square(row, col) for col in range(8)] for row in range(8)]
    return board

def test_50_move_rule():
    """ Verify the game correctly triggers a draw after 50 full moves (100 half-moves) without captures or pawn pushes. """
    game = Game() # Standard starting board
    
    # Simulate a clock reaching 100 half-moves
    game.half_move_clock = 100
    status = game.check_game_over()
    assert status == "Draw! (50-Move Rule)"

    # Ensure the game continues uninterrupted at 99 half-moves
    game.half_move_clock = 99
    assert game.check_game_over() is False

def test_threefold_repetition():
    """ Verify a draw is declared when the exact same board state occurs 3 times. """
    game = Game()
    
    # The initial state is stored in position_history during Game initialization
    
    # Sequence 1: Knights jump out and back in
    game.make_move((7, 6), (5, 5)) # White knight out
    game.make_move((0, 1), (2, 2)) # Black knight out
    game.make_move((5, 5), (7, 6)) # White knight returns
    game.make_move((2, 2), (0, 1)) # Black knight returns (State repeated for the 2nd time)
    
    assert game.check_game_over() is False # 2 occurrences is not a draw
    
    # Sequence 2: Knights jump out and back in again
    game.make_move((7, 6), (5, 5))
    game.make_move((0, 1), (2, 2))
    game.make_move((5, 5), (7, 6))
    game.make_move((2, 2), (0, 1)) # State repeated for the 3rd time
    
    status = game.check_game_over()
    assert status == "Draw! (Threefold Repetition)"

def test_insufficient_material_king_vs_king():
    """ Verify a bare King vs King scenario triggers an immediate draw. """
    game = Game()
    game.board = create_empty_board()
    
    game.board.get_square(7, 4).set_piece(King("white", (7, 4)))
    game.board.get_square(0, 4).set_piece(King("black", (0, 4)))
    game.init_bitboards()
    
    status = game.check_game_over()
    assert status == "Draw! (Insufficient Material)"

def test_insufficient_material_king_and_knight():
    """ Verify a King and Knight vs King scenario triggers a draw (cannot force mate). """
    game = Game()
    game.board = create_empty_board()
    
    game.board.get_square(7, 4).set_piece(King("white", (7, 4)))
    game.board.get_square(0, 4).set_piece(King("black", (0, 4)))
    game.board.get_square(2, 2).set_piece(Knight("white", (2, 2))) # Only one minor piece
    game.init_bitboards()
    
    status = game.check_game_over()
    assert status == "Draw! (Insufficient Material)"

def test_sufficient_material_with_rook():
    """ Verify a King and Rook vs King scenario allows the game to continue. """
    game = Game()
    game.board = create_empty_board()
    
    game.board.get_square(7, 4).set_piece(King("white", (7, 4)))
    game.board.get_square(0, 4).set_piece(King("black", (0, 4)))
    game.board.get_square(2, 2).set_piece(Rook("white", (2, 2))) # Rook is sufficient for mate
    game.init_bitboards()
    
    # Verify the game does not stop
    assert game.check_game_over() is False