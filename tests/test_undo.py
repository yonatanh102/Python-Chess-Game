import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Game import Game
from Queen import Queen

def test_undo_restores_bitboards_basic():
    """ Verify that undoing a standard move fully restores core bitboards. """
    game = Game()
    white_bb_before = game.white_bb
    black_bb_before = game.black_bb
    occ_before = game.occupied_bb
    
    game.make_move((6, 4), (4, 4))
    game.undo_move()
    
    assert game.white_bb == white_bb_before
    assert game.black_bb == black_bb_before
    assert game.occupied_bb == occ_before

def test_undo_restores_capture():
    """ Verify that undoing a capture accurately restores the captured bit. """
    game = Game()
    
    queen = Queen("white", (4, 4))
    game.board.get_square(4, 4).set_piece(queen)
    game.init_bitboards()
    
    w_bb = game.white_bb
    b_bb = game.black_bb
    occ = game.occupied_bb
    
    # Execute a capture
    game.make_move((4, 4), (1, 3))
    game.undo_move()
    
    assert game.white_bb == w_bb
    assert game.black_bb == b_bb
    assert game.occupied_bb == occ

def test_undo_castling():
    """ Verify that undoing a castling move restores both King and Rook bits. """
    game = Game()
    
    # Clear pieces to allow kingside castling
    game.board.get_square(7, 5).remove_piece()
    game.board.get_square(7, 6).remove_piece()
    game.init_bitboards()
    
    w_bb = game.white_bb
    
    # Execute castling
    game.make_move((7, 4), (7, 6))
    game.undo_move()
    
    assert game.white_bb == w_bb