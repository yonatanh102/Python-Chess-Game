
import math

# === 1. GLOBALS & CACHE ===
# The Transposition Table stores previously calculated board evaluations.
# Key: Zobrist Hash (64-bit int), Value: (depth, score, flag)
TRANSPOSITION_TABLE = {}

PIECE_VALUES = {
    "Pawn": 100,
    "Knight": 320,
    "Bishop": 330,
    "Rook": 500,
    "Queen": 900,
    "King": 20000
}

# === 2. PIECE-SQUARE TABLES (PST) ===
# These tables give positional bonuses/penalties to pieces based on their location.
# Oriented for White (row 0 is Black's back rank, row 7 is White's back rank).
PAWN_PST = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [ 5,  5, 10, 25, 25, 10,  5,  5],
    [ 0,  0,  0, 20, 20,  0,  0,  0],
    [ 5, -5,-10,  0,  0,-10, -5,  5],
    [ 5, 10, 10,-20,-20, 10, 10,  5],
    [ 0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_PST = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

BISHOP_PST = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

KING_PST = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20]
]

PST_MAP = {
    "Pawn": PAWN_PST,
    "Knight": KNIGHT_PST,
    "Bishop": BISHOP_PST,
    "King": KING_PST
}


# === 3. EVALUATION FUNCTION ===
def evaluate_board(game):
    """
    Massive Optimization: Iterates ONLY over occupied bitboards instead of an 8x8 grid.
    Positive score = White advantage. Negative score = Black advantage.
    """
    score = 0
    
    # 1. Evaluate White Pieces
    for row, col in game.bb_engine.get_coords_list(game.white_bb):
        piece = game.board.get_piece(row, col)
        if piece:
            val = PIECE_VALUES.get(piece.name, 0)
            if piece.name in PST_MAP:
                val += PST_MAP[piece.name][row][col]
            score += val
            
    # 2. Evaluate Black Pieces
    for row, col in game.bb_engine.get_coords_list(game.black_bb):
        piece = game.board.get_piece(row, col)
        if piece:
            val = PIECE_VALUES.get(piece.name, 0)
            if piece.name in PST_MAP:
                val += PST_MAP[piece.name][7 - row][col]
            score -= val

    return score


# === 4. MOVE GENERATION & ORDERING ===
def get_all_moves_with_start(game, color):
    """
    Retrieves all legal moves for a given color using Bitboard coordinates, 
    ordered by MVV-LVA to maximize Alpha-Beta pruning efficiency.
    """
    moves = []
    my_bb = game.white_bb if color == "white" else game.black_bb
    
    # Iterate only over active pieces via bitboard
    for row, col in game.bb_engine.get_coords_list(my_bb):
        piece = game.board.get_piece(row, col)
        if piece and piece.color == color:
            legal_ends = game.get_legal_moves(piece)
            for end in legal_ends:
                moves.append(((row, col), end))

    def mvv_lva_score(move):
        start, end = move
        attacker = game.board.get_piece(start[0], start[1])
        victim = game.board.get_piece(end[0], end[1])

        if victim:
            victim_val = PIECE_VALUES.get(victim.name, 0)
            attacker_val = PIECE_VALUES.get(attacker.name, 0)
            
            # Prioritize captures (base 10000), favor high-value victims (MVV), 
            # and break ties by preferring low-value attackers (LVA).
            return 10000 + (victim_val * 10) - attacker_val
        
        return 0

    moves.sort(key=mvv_lva_score, reverse=True)
    return moves


# === 5. MINIMAX ALGORITHM (Alpha-Beta & Transposition Table) ===
def minimax(game, depth, alpha, beta, is_maxing):
    global TRANSPOSITION_TABLE
    hash_key = game.zobrist_hash

    # 1. Transposition Table Lookup (Cache hit)
    if hash_key in TRANSPOSITION_TABLE:
        tt_depth, tt_score, tt_flag = TRANSPOSITION_TABLE[hash_key]
        if tt_depth >= depth:
            if tt_flag == 'EXACT':
                return tt_score
            elif tt_flag == 'LOWERBOUND':
                alpha = max(alpha, tt_score)
            elif tt_flag == 'UPPERBOUND':
                beta = min(beta, tt_score)

            # Cutoff from cached bounds
            if alpha >= beta:
                return tt_score

    # 2. Technical Draw Detection
    if getattr(game, 'half_move_clock', 0) >= 100 or \
       getattr(game, 'position_history', []).count(hash_key) >= 3 or \
       game.has_insufficient_material():
        return 0

    # 3. Base Case: Max depth reached
    if depth == 0:
        return evaluate_board(game)

    orig_alpha = alpha
    orig_beta = beta
    color = "white" if is_maxing else "black"
    moves = get_all_moves_with_start(game, color)

    # Checkmate / Stalemate detection
    if not moves:
        if game.is_in_check(color):
            return -99999 if is_maxing else 99999
        return 0

    # 4. Maximizing Player (White)
    if is_maxing:
        max_eval = -math.inf
        for start, end in moves:
            game.make_move(start, end)
            eval_score = minimax(game, depth - 1, alpha, beta, False)
            game.undo_move()

            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Alpha-Beta Cutoff

        # Store result in TT
        tt_flag = 'UPPERBOUND' if max_eval <= orig_alpha else ('LOWERBOUND' if max_eval >= beta else 'EXACT')
        TRANSPOSITION_TABLE[hash_key] = (depth, max_eval, tt_flag)
        return max_eval

    # 5. Minimizing Player (Black)
    else:
        min_eval = math.inf
        for start, end in moves:
            game.make_move(start, end)
            eval_score = minimax(game, depth - 1, alpha, beta, True)
            game.undo_move()

            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Alpha-Beta Cutoff

        # Store result in TT
        tt_flag = 'LOWERBOUND' if min_eval >= orig_beta else ('UPPERBOUND' if min_eval <= alpha else 'EXACT')
        TRANSPOSITION_TABLE[hash_key] = (depth, min_eval, tt_flag)
        return min_eval    


# === 6. AI ENTRY POINT ===
def get_best_move(game, depth, ai_color):
    """
    Simulates all possible moves for the root position and 
    selects the one with the best minimax score.
    """
    TRANSPOSITION_TABLE.clear() # Prevent memory leaks between turns
    
    best_move = None
    alpha = -math.inf
    beta = math.inf
    is_maximizing = (ai_color == "white")
    best_value = -math.inf if is_maximizing else math.inf
    
    moves = get_all_moves_with_start(game, ai_color)

    for start, end in moves:
        game.make_move(start, end)
        board_value = minimax(game, depth - 1, alpha, beta, not is_maximizing)
        game.undo_move()

        if is_maximizing:
            if board_value > best_value:
                best_value = board_value
                best_move = (start, end)
            alpha = max(alpha, best_value)
        else:
            if board_value < best_value:
                best_value = board_value
                best_move = (start, end)
            beta = min(beta, best_value)

        if beta <= alpha:
            break

    return best_move