import pytest
import sys
import os
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Game import Game
from Queen import Queen
from King import King
from Rook import Rook
from Square import Square
from Board import Board
from AI import get_best_move, evaluate_board

def create_empty_board():
    """ Helper function: Creates a completely empty board for isolated AI testing. """
    board = Board()
    board.grid = [[Square(row, col) for col in range(8)] for row in range(8)]
    return board

def test_ai_finds_mate_in_one():
    """ Verify the AI will immediately play a winning move if one is available. """
    game = Game()
    game.board = create_empty_board()
    game.turn = "white"

    # Setup a mate-in-one scenario
    game.board.get_square(0, 7).set_piece(King("black", (0, 7)))
    game.board.get_square(2, 5).set_piece(King("white", (2, 5)))
    game.board.get_square(2, 6).set_piece(Queen("white", (2, 6)))
    game.init_bitboards()

    # The AI should move the Queen from (2, 6) to (1, 6) to deliver checkmate
    best_move = get_best_move(game, depth=2, ai_color="white")
    assert best_move == ((2, 6), (1, 6))

def test_ai_avoids_blunder():
    """ Verify the AI will not blindly sacrifice a high-value piece. """
    game = Game()
    game.board = create_empty_board()
    game.turn = "white"

    # White Queen is safe at (7, 0). Black Rook controls the top of the A-file.
    game.board.get_square(7, 0).set_piece(Queen("white", (7, 0)))
    game.board.get_square(7, 7).set_piece(King("white", (7, 7)))
    game.board.get_square(0, 0).set_piece(Rook("black", (0, 0)))
    game.board.get_square(0, 7).set_piece(King("black", (0, 7)))
    game.init_bitboards()

    # The AI should realize that moving the Queen up the A-file hangs it to the Rook
    best_move = get_best_move(game, depth=2, ai_color="white")
    assert best_move != ((7, 0), (1, 0))
    assert best_move != ((7, 0), (2, 0))

def test_evaluation_symmetry():
    """ Verify the static evaluation function mirrors perfectly for both colors. """
    # Game 1: White Queen vs Black Rook
    game1 = Game()
    game1.board = create_empty_board()
    game1.board.get_square(4, 4).set_piece(Queen("white", (4, 4)))
    game1.board.get_square(0, 0).set_piece(Rook("black", (0, 0)))

    # Game 2: Black Queen vs White Rook
    game2 = Game()
    game2.board = create_empty_board()
    game2.board.get_square(4, 4).set_piece(Queen("black", (4, 4)))
    game2.board.get_square(0, 0).set_piece(Rook("white", (0, 0)))

    score1 = evaluate_board(game1)
    score2 = evaluate_board(game2)

    assert score1 > 0 # White is winning in Game 1
    assert score2 < 0 # Black is winning in Game 2
    assert score1 == -score2 # The magnitude of the advantage must be identical