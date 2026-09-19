import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from FastBitboard import BitboardEngine

def create_empty_engine():
    """ Helper function: Creates a BitboardEngine with all 64-bit integers set to 0. """
    engine = BitboardEngine()
    engine.white_pawns = engine.white_knights = engine.white_bishops = 0
    engine.white_rooks = engine.white_queens = engine.white_king = 0
    engine.black_pawns = engine.black_knights = engine.black_bishops = 0
    engine.black_rooks = engine.black_queens = engine.black_king = 0
    return engine

def test_pawn_pushes():
    """ Verify pawn forward movement and block detection. """
    engine = create_empty_engine()
    
    # Place a white pawn at D2 (row 6, col 3)
    pawn_index = engine.get_index(6, 3)
    engine.white_pawns = engine.set_piece(engine.white_pawns, pawn_index)
    
    pushes = engine.get_white_pawn_pushes()
    
    # The pawn should be able to move to D3 (row 5, col 3)
    target_index = engine.get_index(5, 3)
    assert engine.check_square(pushes, target_index) is True
    
    # Place a blocking black piece directly in front of it at D3
    engine.black_rooks = engine.set_piece(engine.black_rooks, target_index)
    
    # Recalculate pushes - the pawn should now be completely blocked
    blocked_pushes = engine.get_white_pawn_pushes()
    assert blocked_pushes == 0

def test_knight_moves_and_wrapping():
    """ Verify Knight moves and ensure they do not wrap across the board edges. """
    engine = create_empty_engine()
    
    # Place a white knight on the H-file edge (row 4, col 7)
    knight_index = engine.get_index(4, 7)
    engine.white_knights = engine.set_piece(engine.white_knights, knight_index)
    
    friendly = engine.get_all_white_pieces()
    moves = engine.get_knight_moves(engine.white_knights, friendly)
    
    valid_targets = [
        engine.get_index(3, 5), engine.get_index(5, 5),
        engine.get_index(2, 6), engine.get_index(6, 6)
    ]
    
    for target in valid_targets:
        assert engine.check_square(moves, target) is True
        
    # Verify that the shift DID NOT wrap around to the A-file
    invalid_wrap = engine.get_index(3, 0)
    assert engine.check_square(moves, invalid_wrap) is False

def test_rook_ray_casting():
    """ Verify Rook sliding logic stops at blockers and captures enemies. """
    engine = create_empty_engine()
    
    # Place white rook in the middle at E4
    rook_index = engine.get_index(4, 4)
    engine.white_rooks = engine.set_piece(engine.white_rooks, rook_index)
    
    # Place a friendly blocker at G4
    friendly_index = engine.get_index(4, 6)
    engine.white_pawns = engine.set_piece(engine.white_pawns, friendly_index)
    
    # Place an enemy target at B4
    enemy_index = engine.get_index(4, 1)
    engine.black_pawns = engine.set_piece(engine.black_pawns, enemy_index)
    
    friendly_board = engine.get_all_white_pieces()
    empty_sq = ~engine.get_occupied_squares() & 0xFFFFFFFFFFFFFFFF
    moves = engine.get_rook_moves(engine.white_rooks, friendly_board, empty_sq)
    
    # Rightward: Valid at F4, blocked by friendly at G4 and beyond
    assert engine.check_square(moves, engine.get_index(4, 5)) is True
    assert engine.check_square(moves, engine.get_index(4, 6)) is False
    assert engine.check_square(moves, engine.get_index(4, 7)) is False
    
    # Leftward: Valid at D4, C4, captures B4, blocked from reaching A4
    assert engine.check_square(moves, engine.get_index(4, 3)) is True
    assert engine.check_square(moves, engine.get_index(4, 2)) is True
    assert engine.check_square(moves, engine.get_index(4, 1)) is True
    assert engine.check_square(moves, engine.get_index(4, 0)) is False

def test_bishop_ray_casting():
    """ Verify Bishop sliding logic operates strictly diagonally. """
    engine = create_empty_engine()
    
    # Place bishop at D4
    bishop_index = engine.get_index(4, 3)
    engine.white_bishops = engine.set_piece(engine.white_bishops, bishop_index)
    
    friendly_board = engine.get_all_white_pieces()
    empty_sq = ~engine.get_occupied_squares() & 0xFFFFFFFFFFFFFFFF
    moves = engine.get_bishop_moves(engine.white_bishops, friendly_board, empty_sq)
    
    # Diagonal movement
    assert engine.check_square(moves, engine.get_index(3, 4)) is True
    assert engine.check_square(moves, engine.get_index(2, 5)) is True
    assert engine.check_square(moves, engine.get_index(5, 2)) is True
    
    # Must not contain straight moves
    assert engine.check_square(moves, engine.get_index(4, 4)) is False

def test_king_moves():
    """ Verify King logic respects board corners. """
    engine = create_empty_engine()
    
    # Place white king at A1 corner
    king_index = engine.get_index(7, 0)
    engine.white_king = engine.set_piece(engine.white_king, king_index)
    
    friendly = engine.get_all_white_pieces()
    moves = engine.get_king_moves(engine.white_king, friendly)
    
    # A king in the corner should only have 3 valid targets
    assert engine.check_square(moves, engine.get_index(6, 0)) is True
    assert engine.check_square(moves, engine.get_index(6, 1)) is True
    assert engine.check_square(moves, engine.get_index(7, 1)) is True
    
    # Verify no wrapping occurred to the H-file
    assert engine.check_square(moves, engine.get_index(7, 7)) is False

def test_white_pawn_moves_and_blocks():
    """ Verify white pawns can push but respect blockers. """
    engine = create_empty_engine()
    pawn_idx = engine.get_index(6, 3) # D2
    engine.white_pawns = engine.set_piece(engine.white_pawns, pawn_idx)
    
    blocker_idx = engine.get_index(4, 3) # D4
    engine.black_rooks = engine.set_piece(engine.black_rooks, blocker_idx)
    
    empty_sq = ~engine.get_occupied_squares() & 0xFFFFFFFFFFFFFFFF
    moves = engine.get_white_pawn_moves(engine.white_pawns, empty_sq, engine.get_all_black_pieces())
    
    assert engine.check_square(moves, engine.get_index(5, 3)) is True
    assert engine.check_square(moves, engine.get_index(4, 3)) is False

def test_black_pawn_attacks():
    """ Verify black pawns move 'down' the board and capture diagonally. """
    engine = create_empty_engine()
    pawn_idx = engine.get_index(1, 4) # E7
    engine.black_pawns = engine.set_piece(engine.black_pawns, pawn_idx)
    
    target1 = engine.get_index(2, 3) # D6
    target2 = engine.get_index(2, 5) # F6
    engine.white_knights = engine.set_piece(engine.white_knights, target1)
    engine.white_knights = engine.set_piece(engine.white_knights, target2)
    
    empty_sq = ~engine.get_occupied_squares() & 0xFFFFFFFFFFFFFFFF
    moves = engine.get_black_pawn_moves(engine.black_pawns, empty_sq, engine.get_all_white_pieces())
    
    assert engine.check_square(moves, target1) is True # Left capture
    assert engine.check_square(moves, target2) is True # Right capture
    assert engine.check_square(moves, engine.get_index(2, 4)) is True # Straight push

def test_queen_moves():
    """ Verify Queen combines Rook and Bishop rays accurately. """
    engine = create_empty_engine()
    queen_idx = engine.get_index(4, 4)
    engine.white_queens = engine.set_piece(engine.white_queens, queen_idx)
    
    friendly = engine.get_all_white_pieces()
    empty_sq = ~engine.get_occupied_squares() & 0xFFFFFFFFFFFFFFFF
    moves = engine.get_queen_moves(engine.white_queens, friendly, empty_sq)
    
    assert engine.check_square(moves, engine.get_index(4, 0)) is True # Straight
    assert engine.check_square(moves, engine.get_index(0, 0)) is True # Diagonal
    assert engine.check_square(moves, engine.get_index(7, 4)) is True # Straight

def test_a_file_wrapping():
    """ Secondary verification for A-file wrap prevention on Knights. """
    engine = create_empty_engine()
    knight_idx = engine.get_index(4, 0)
    engine.white_knights = engine.set_piece(engine.white_knights, knight_idx)
    
    moves = engine.get_knight_moves(engine.white_knights, engine.get_all_white_pieces())
    
    assert engine.check_square(moves, engine.get_index(3, 7)) is False
    assert engine.check_square(moves, engine.get_index(5, 7)) is False