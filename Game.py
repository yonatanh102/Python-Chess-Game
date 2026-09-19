
from Board import Board
from Queen import Queen
from FastBitboard import BitboardEngine
import random

# === 1. ZOBRIST HASHING GLOBALS ===
ZOBRIST_KEYS = {}
for piece in ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']:
    for color in ['white', 'black']:
        ZOBRIST_KEYS[(piece, color)] = [random.getrandbits(64) for _ in range(64)]

ZOBRIST_TURN = random.getrandbits(64)
ZOBRIST_CASTLING = {
    'wk': random.getrandbits(64), 'wq': random.getrandbits(64),
    'bk': random.getrandbits(64), 'bq': random.getrandbits(64)
}
ZOBRIST_EN_PASSANT = [random.getrandbits(64) for _ in range(8)]


class Game:

    # === 2. INITIALIZATION ===
    def __init__(self):
        self.board = Board()
        self.turn = "white"
        self.move_history = []
        self.bb_engine = BitboardEngine()
        self.init_bitboards()

    def init_bitboards(self):
        self.white_bb = 0
        self.black_bb = 0
        self.zobrist_hash = 0
        
        # O(1) tracking for kings to instantly evaluate checks
        self.king_pos = {"white": None, "black": None}

        for r in range(8):
            for c in range(8):
                p = self.board.get_piece(r, c)
                if p:
                    idx = self.bb_engine.get_index(r, c)
                    bit = 1 << idx
                    if p.color == "white":
                        self.white_bb |= bit
                    else:
                        self.black_bb |= bit

                    self.zobrist_hash ^= ZOBRIST_KEYS[(p.name, p.color)][idx]
                    
                    if p.name == "King":
                        self.king_pos[p.color] = (r, c)

        self.occupied_bb = self.white_bb | self.black_bb
        
        if self.turn == "black":
            self.zobrist_hash ^= ZOBRIST_TURN

        rights = self._get_castling_rights()
        for key, has_right in rights.items():
            if has_right:
                self.zobrist_hash ^= ZOBRIST_CASTLING[key]

        ep = getattr(self.board, 'en_passant_target', None)
        if ep:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[ep[1]]

        self.half_move_clock = 0
        self.position_history = [self.zobrist_hash]


    # === 3. CORE MOVE EXECUTION (make / undo) ===
    def make_move(self, start, end):
        old_rights = self._get_castling_rights()
        old_ep = getattr(self.board, 'en_passant_target', None)
        
        row, col = start
        target_row, target_col = end

        moved_piece = self.board.get_piece(row, col)
        captured_piece = self.board.get_piece(target_row, target_col)
        piece_had_moved = moved_piece.has_moved if moved_piece else False
        castling_info = None

        prev_en_passant = getattr(self.board, 'en_passant_target', None)
        is_en_passant = False
        if moved_piece and moved_piece.name == "Pawn" and (target_row, target_col) == prev_en_passant:
            is_en_passant = True
            captured_piece = self.board.get_piece(row, target_col)
            self.board.get_square(row, target_col).remove_piece()

        is_castling = False
        if moved_piece and moved_piece.name == "King" and abs(col - target_col) == 2:
            is_castling = True
            if target_col > col:
                rook_start = (row, 7)
                rook_end = (row, target_col - 1)
            else:
                rook_start = (row, 0)
                rook_end = (row, target_col + 1)

            rook = self.board.get_piece(*rook_start)
            castling_info = (rook_start, rook_end, rook, rook.has_moved if rook else False)
            
            self.board.get_square(*rook_start).remove_piece()
            self.board.get_square(*rook_end).set_piece(rook)
            if rook:
                rook.has_moved = True

        move_data = {
            'start': start,
            'end': end,
            'moved_piece': moved_piece,
            'captured_piece': captured_piece,
            'piece_had_moved': piece_had_moved,
            'is_castling': is_castling,
            'prev_en_passant': prev_en_passant,
            'is_en_passant': is_en_passant,
            'castling_info': castling_info,
            'half_move_clock': getattr(self, 'half_move_clock', 0),
            'old_king_pos': dict(self.king_pos) # O(1) saving the kings positions
        }
        self.move_history.append(move_data)

        self.board.get_square(row, col).remove_piece()
        self.board.get_square(target_row, target_col).set_piece(moved_piece)
        if moved_piece:
            moved_piece.has_moved = True
            
        # O(1) updating the king's new position
        if moved_piece and moved_piece.name == "King":
            self.king_pos[moved_piece.color] = (target_row, target_col)

        is_promotion = False
        if moved_piece and moved_piece.name == "Pawn":
            if (moved_piece.color == "white" and target_row == 0) or \
               (moved_piece.color == "black" and target_row == 7):
                is_promotion = True
                promote_queen = Queen(moved_piece.color, (target_row, target_col))
                self.board.get_square(target_row, target_col).set_piece(promote_queen)

        if moved_piece and moved_piece.name == 'Pawn' and abs(target_row - row) == 2:
            self.board.en_passant_target = ((row + target_row) // 2, col)
        else:
            self.board.en_passant_target = None

        self.toggle_bit(moved_piece.name, moved_piece.color, row, col)
        
        if is_promotion:
            self.toggle_bit("Queen", moved_piece.color, target_row, target_col)
        else:
            self.toggle_bit(moved_piece.name, moved_piece.color, target_row, target_col)

        if captured_piece:
            cap_r, cap_c = (row, target_col) if is_en_passant else (target_row, target_col)
            self.toggle_bit(captured_piece.name, captured_piece.color, cap_r, cap_c)

        if is_castling:
            rook_start, rook_end, rook, _ = castling_info
            self.toggle_bit("Rook", rook.color, rook_start[0], rook_start[1])
            self.toggle_bit("Rook", rook.color, rook_end[0], rook_end[1])

        self.occupied_bb = self.white_bb | self.black_bb

        new_rights = self._get_castling_rights()
        new_ep = getattr(self.board, 'en_passant_target', None)

        for key in old_rights:
            if old_rights[key] != new_rights[key]:
                self.zobrist_hash ^= ZOBRIST_CASTLING[key]

        if old_ep:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[old_ep[1]]
        if new_ep:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[new_ep[1]]

        if (moved_piece and moved_piece.name == 'Pawn') or captured_piece:
            self.half_move_clock = 0
        else:
            self.half_move_clock += 1
            
        self.position_history.append(self.zobrist_hash)

    def undo_move(self):
        if not self.move_history:
            return
        
        old_rights = self._get_castling_rights()
        old_ep = getattr(self.board, 'en_passant_target', None)
        
        move_data = self.move_history.pop()
        start = move_data['start']
        end = move_data['end']
        moved_piece = move_data['moved_piece']
        captured_piece = move_data['captured_piece']
        castling_info = move_data.get('castling_info')

        row, col = start
        target_row, target_col = end
        self.board.en_passant_target = move_data['prev_en_passant']

        if moved_piece:
            moved_piece.has_moved = move_data['piece_had_moved']

        # O(1) revert the kings position
        self.king_pos = move_data['old_king_pos']

        self.board.get_square(row, col).set_piece(moved_piece)
        target_square = self.board.get_square(target_row, target_col)

        if move_data['is_en_passant']:
            target_square.remove_piece()
            self.board.get_square(row, target_col).set_piece(captured_piece)
        else:
            if captured_piece:
                target_square.set_piece(captured_piece)
            else:
                target_square.remove_piece()

        if castling_info:
            rook_start, rook_end, rook, rook_had_moved = castling_info
            self.board.get_square(*rook_end).remove_piece()
            self.board.get_square(*rook_start).set_piece(rook)
            if rook:
                rook.has_moved = rook_had_moved

        is_promotion = moved_piece.name == "Pawn" and target_row in (0, 7)
        
        if is_promotion:
            self.toggle_bit("Queen", moved_piece.color, target_row, target_col)
        else:
            self.toggle_bit(moved_piece.name, moved_piece.color, target_row, target_col)
            
        self.toggle_bit(moved_piece.name, moved_piece.color, row, col)
        
        if captured_piece:
            cap_r, cap_c = (row, target_col) if move_data['is_en_passant'] else (target_row, target_col)
            self.toggle_bit(captured_piece.name, captured_piece.color, cap_r, cap_c)
        
        if castling_info:
            rook_start, rook_end, rook, _ = castling_info
            self.toggle_bit("Rook", rook.color, rook_end[0], rook_end[1])
            self.toggle_bit("Rook", rook.color, rook_start[0], rook_start[1])

        self.occupied_bb = self.white_bb | self.black_bb

        new_rights = self._get_castling_rights()
        new_ep = getattr(self.board, 'en_passant_target', None)

        for key in old_rights:
            if old_rights[key] != new_rights[key]:
                self.zobrist_hash ^= ZOBRIST_CASTLING[key]

        if old_ep:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[old_ep[1]]
        if new_ep:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[new_ep[1]]

        if self.position_history:
            self.position_history.pop()
        self.half_move_clock = move_data['half_move_clock']

    def switch_turn(self):
        self.turn = "black" if self.turn == "white" else "white"
        self.zobrist_hash ^= ZOBRIST_TURN


    # === 4. STATE VALIDATION & DRAW RULES ===
    def toggle_bit(self, piece_name, color, row, col):
        idx = self.bb_engine.get_index(row, col)
        bit = 1 << idx
        
        if color == "white":
            self.white_bb ^= bit
        else:
            self.black_bb ^= bit

        self.zobrist_hash ^= ZOBRIST_KEYS[(piece_name, color)][idx]

    def _get_castling_rights(self):
        rights = {'wk': False, 'wq': False, 'bk': False, 'bq': False}
        wk = self.board.get_piece(7, 4)
        if wk and wk.name == "King" and wk.color == "white" and not getattr(wk, 'has_moved', False):
            wrk = self.board.get_piece(7, 7)
            if wrk and wrk.name == "Rook" and wrk.color == "white" and not getattr(wrk, 'has_moved', False):
                rights["wk"] = True
            wrq = self.board.get_piece(7, 0)
            if wrq and wrq.name == "Rook" and wrq.color == "white" and not getattr(wrq, 'has_moved', False):
                rights["wq"] = True

        bk = self.board.get_piece(0, 4)
        if bk and bk.name == "King" and bk.color == "black" and not getattr(bk, 'has_moved', False):
            brk = self.board.get_piece(0, 7)
            if brk and brk.name == "Rook" and brk.color == "black" and not getattr(brk, 'has_moved', False):
                rights["bk"] = True
            brq = self.board.get_piece(0, 0)
            if brq and brq.name == "Rook" and brq.color == "black" and not getattr(brq, 'has_moved', False):
                rights["bq"] = True

        return rights

    def has_insufficient_material(self):
        if self.occupied_bb.bit_count() > 3:
            return False
        if self.occupied_bb.bit_count() == 2:
            return True
            
        for i in range(64):
            if(self.occupied_bb & (1 << i)) != 0:
                r, c = i // 8, i % 8
                p = self.board.get_piece(r, c)
                if p and p.name not in ["King", "Knight", "Bishop"]:
                    return False
        return True

    def is_in_check(self, color):
        """ 
        Massive Optimization: Uses tracked king positions and iterates ONLY over 
        active enemy pieces via bitboards, eliminating the 8x8 full board scan.
        """
        king_pos = self.king_pos[color]
        if not king_pos:
            return False
            
        king_idx = self.bb_engine.get_index(king_pos[0], king_pos[1])
        king_bit = 1 << king_idx
        
        enemy_color = "black" if color == "white" else "white"
        friendly_for_enemy = self.black_bb if enemy_color == "black" else self.white_bb
        empty_bb = ~self.occupied_bb & 0xFFFFFFFFFFFFFFFF
        
        enemy_bb = self.black_bb if color == "white" else self.white_bb

        # Loop ONLY through coordinates where enemy pieces actually exist
        for row, col in self.bb_engine.get_coords_list(enemy_bb):
            piece = self.board.get_piece(row, col)
            if piece and piece.color == enemy_color:
                piece_idx = self.bb_engine.get_index(row, col)
                piece_bb = 1 << piece_idx
                moves_bb = 0

                if piece.name == "Pawn":
                    if piece.color == "white":
                        moves_bb = self.bb_engine.get_white_pawn_moves(piece_bb, empty_bb, self.black_bb)
                    else:
                        moves_bb = self.bb_engine.get_black_pawn_moves(piece_bb, empty_bb, self.white_bb)
                elif piece.name == "Knight":
                    moves_bb = self.bb_engine.get_knight_moves(piece_bb, friendly_for_enemy)
                elif piece.name == "Rook":
                    moves_bb = self.bb_engine.get_rook_moves(piece_bb, friendly_for_enemy, empty_bb)
                elif piece.name == "Bishop":
                    moves_bb = self.bb_engine.get_bishop_moves(piece_bb, friendly_for_enemy, empty_bb)
                elif piece.name == "Queen":
                    moves_bb = self.bb_engine.get_queen_moves(piece_bb, friendly_for_enemy, empty_bb)
                elif piece.name == "King":
                    moves_bb = self.bb_engine.get_king_moves(piece_bb, friendly_for_enemy)

                if (moves_bb & king_bit) != 0:
                    return True

        return False

    def check_game_over(self):
        legal_moves = self.get_all_legal_moves(self.turn)

        if len(legal_moves) == 0:
            if self.is_in_check(self.turn):
                winner = "White" if self.turn == "black" else "Black"
                return f"Checkmate! {winner} wins!"
            else:
                return "Stalemate! It's a draw."

        if getattr(self, 'half_move_clock', 0) >= 100:
            return "Draw! (50-Move Rule)"
        if getattr(self, 'position_history', []).count(self.zobrist_hash) >= 3:
            return "Draw! (Threefold Repetition)"
        if self.has_insufficient_material():
            return "Draw! (Insufficient Material)"
            
        return False


    # === 5. MOVE GENERATION & VALIDATION ===
    def get_legal_moves(self, piece):
        legal_moves = []
        currently_in_check = None
        pseudo_moves = self.get_bb_pseudo_moves(piece)
        start_pos = piece.position

        for end_pos in pseudo_moves:
            if piece.name == "King" and abs(start_pos[1] - end_pos[1]) == 2:
                if currently_in_check is None:
                    currently_in_check = self.is_in_check(piece.color)
                if currently_in_check:
                    continue

                step = 1 if end_pos[1] > start_pos[1] else -1
                middle_col = start_pos[1] + step
                self.make_move(start_pos, (start_pos[0], middle_col))
                middle_in_check = self.is_in_check(piece.color)
                self.undo_move()

                if middle_in_check:
                    continue

            self.make_move(start_pos, end_pos)
            if not self.is_in_check(piece.color):
                legal_moves.append(end_pos)
            self.undo_move()

        return legal_moves

    def get_all_legal_moves(self, color):
        """ 
        Massive Optimization: Iterates ONLY over the player's active pieces 
        using Bitboards instead of an 8x8 full board scan.
        """
        all_moves = []
        my_bb = self.white_bb if color == "white" else self.black_bb
        
        for row, col in self.bb_engine.get_coords_list(my_bb):
            piece = self.board.get_piece(row, col)
            if piece and piece.color == color:
                all_moves.extend(self.get_legal_moves(piece))
                
        return all_moves

    def get_bb_pseudo_moves(self, piece):
        if piece.name == "King":
            return piece.get_valid_moves(self.board)

        piece_idx = self.bb_engine.get_index(piece.position[0], piece.position[1])
        piece_bb = 1 << piece_idx

        friendly_bb = self.white_bb if piece.color == "white" else self.black_bb
        enemy_bb = self.black_bb if piece.color == "white" else self.white_bb
        occupied_bb = self.occupied_bb
        empty_bb = ~occupied_bb & 0xFFFFFFFFFFFFFFFF
        moves_bb = 0

        if piece.name == "Pawn":
            if piece.color == "white":
                moves_bb = self.bb_engine.get_white_pawn_moves(piece_bb, empty_bb, enemy_bb)
            else: 
                moves_bb = self.bb_engine.get_black_pawn_moves(piece_bb, empty_bb, enemy_bb)

            coords = self.bb_engine.get_coords_list(moves_bb)
            if getattr(self.board, 'en_passant_target', None):
                ep_r, ep_c = self.board.en_passant_target
                if abs(piece.position[1] - ep_c) == 1:
                    if (piece.color == "white" and piece.position[0] - ep_r == 1) or \
                       (piece.color == "black" and ep_r - piece.position[0] == 1):
                        coords.append((ep_r, ep_c))
            return coords
        
        elif piece.name == "Rook":
            moves_bb = self.bb_engine.get_rook_moves(piece_bb, friendly_bb, empty_bb)
        elif piece.name == "Bishop":
            moves_bb = self.bb_engine.get_bishop_moves(piece_bb, friendly_bb, empty_bb)
        elif piece.name == "Queen":
            moves_bb = self.bb_engine.get_queen_moves(piece_bb, friendly_bb, empty_bb)
        elif piece.name == "Knight":
            moves_bb = self.bb_engine.get_knight_moves(piece_bb, friendly_bb)

        return self.bb_engine.get_coords_list(moves_bb)

    # === 6. GUI INTERFACE ===
    def move_piece(self, start, end):
        row, col = start
        piece = self.board.get_piece(row, col)

        if piece is None:
            print("Error: There is no piece at this square.")
            return False
        if piece.color != self.turn:
            print(f"Error: It's {self.turn}'s turn, but you chose a {piece.color} piece.")
            return False
        
        valid_moves = self.get_legal_moves(piece)

        if end in valid_moves:
            self.make_move(start, end)
            print(f"Moved {piece.name} to {end}")
            self.switch_turn()
            return True
        else:
            print("Error: Illegal move for this piece.")
            return False