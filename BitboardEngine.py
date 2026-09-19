
# === 1. GLOBAL MASKS (Edge Wrapping Prevention) ===
NOT_A_FILE = 0xFEFEFEFEFEFEFEFE
NOT_H_FILE = 0x7F7F7F7F7F7F7F7F
NOT_AB_FILE = 0xFCFCFCFCFCFCFCFC
NOT_GH_FILE = 0x3F3F3F3F3F3F3F3F


class BitboardEngine:

    # === 2. INITIALIZATION ===
    def __init__(self):
        # 64-bit integers representing standard chess starting piece locations
        
        # Black pieces
        self.black_rooks   = 0x0000000000000081
        self.black_knights = 0x0000000000000042
        self.black_bishops = 0x0000000000000024
        self.black_queens  = 0x0000000000000008
        self.black_king    = 0x0000000000000010
        self.black_pawns   = 0x000000000000FF00

        # White pieces
        self.white_pawns   = 0x00FF000000000000
        self.white_rooks   = 0x8100000000000000
        self.white_knights = 0x4200000000000000
        self.white_bishops = 0x2400000000000000
        self.white_queens  = 0x0800000000000000
        self.white_king    = 0x1000000000000000

    # === 3. BITWISE UTILITIES & MAPPING ===
    def set_piece(self, bitboard, square_index):
        # Turn ON a specific bit using OR
        return bitboard | (1 << square_index)

    def clear_piece(self, bitboard, square_index):
        # Turn OFF a specific bit using AND with NOT
        return bitboard & ~(1 << square_index)

    def check_square(self, bitboard, square_index):
        # Check if a specific bit is 1
        return (bitboard & (1 << square_index)) != 0

    def get_index(self, row, col):
        return row * 8 + col

    def get_coords(self, index):
        return index // 8, index % 8

    def get_coords_list(self, bitboard):
        # Scan all 64 bits and return a list of (row, col) tuples for active bits
        coords = []
        for i in range(64):
            if (bitboard & (1 << i)) != 0:
                coords.append((i // 8, i % 8))
        return coords

    # === 4. BOARD STATE AGGREGATORS ===
    def get_all_white_pieces(self):
        return (self.white_pawns | self.white_bishops | self.white_king | 
                self.white_knights | self.white_queens | self.white_rooks)

    def get_all_black_pieces(self):
        return (self.black_pawns | self.black_bishops | self.black_king | 
                self.black_knights | self.black_queens | self.black_rooks)

    def get_occupied_squares(self):
        return self.get_all_white_pieces() | self.get_all_black_pieces()

    # === 5. LEAPING PIECE MOVE GENERATORS ===
    def get_white_pawn_pushes(self):
        empty_squares = ~self.get_occupied_squares() & 0xFFFFFFFFFFFFFFFF
        return (self.white_pawns >> 8) & empty_squares

    def get_white_pawn_moves(self, pawns_bitboard, empty_squares, enemy_pieces):
        single_pushes = (pawns_bitboard >> 8) & empty_squares
        double_pushes = (single_pushes >> 8) & empty_squares & 0x000000FF00000000
        attack_left = (pawns_bitboard >> 9) & NOT_H_FILE & enemy_pieces
        attack_right = (pawns_bitboard >> 7) & NOT_A_FILE & enemy_pieces
        return (single_pushes | double_pushes | attack_left | attack_right) & 0xFFFFFFFFFFFFFFFF

    def get_black_pawn_moves(self, pawns_bitboard, empty_squares, enemy_pieces):
        single_pushes = (pawns_bitboard << 8) & empty_squares
        double_pushes = (single_pushes << 8) & empty_squares & 0x00000000FF000000
        attack_left = (pawns_bitboard << 7) & NOT_H_FILE & enemy_pieces
        attack_right = (pawns_bitboard << 9) & NOT_A_FILE & enemy_pieces
        return (single_pushes | double_pushes | attack_left | attack_right) & 0xFFFFFFFFFFFFFFFF

    def get_king_moves(self, king_bitboard, friendly_pieces_bitboard):
        step_up = king_bitboard >> 8
        step_down = king_bitboard << 8
        step_left = (king_bitboard >> 1) & NOT_H_FILE
        step_right = (king_bitboard << 1) & NOT_A_FILE
        step_up_right = (king_bitboard >> 7) & NOT_A_FILE
        step_up_left = (king_bitboard >> 9) & NOT_H_FILE
        step_down_right = (king_bitboard << 9) & NOT_A_FILE
        step_down_left = (king_bitboard << 7) & NOT_H_FILE

        all_king_targets = (step_down | step_left | step_right | step_up | 
                            step_up_right | step_down_left | step_down_right | step_up_left)

        return (all_king_targets & ~friendly_pieces_bitboard) & 0xFFFFFFFFFFFFFFFF

    def get_knight_moves(self, knight_bitboard, friendly_pieces_bitboard):
        up_up_left = (knight_bitboard >> 17) & NOT_H_FILE
        up_up_right = (knight_bitboard >> 15) & NOT_A_FILE
        up_left_left = (knight_bitboard >> 10) & NOT_GH_FILE
        up_right_right = (knight_bitboard >> 6) & NOT_AB_FILE
        down_down_left = (knight_bitboard << 15) & NOT_H_FILE
        down_down_right = (knight_bitboard << 17) & NOT_A_FILE
        down_left_left = (knight_bitboard << 6) & NOT_GH_FILE
        down_right_right = (knight_bitboard << 10) & NOT_AB_FILE

        all_knights_targets = (up_up_left | up_up_right | up_left_left | up_right_right |
                               down_down_left | down_down_right | down_left_left | down_right_right)

        return (all_knights_targets & ~friendly_pieces_bitboard) & 0xFFFFFFFFFFFFFFFF

    # === 6. SLIDING PIECE MOVE GENERATORS (Ray Casting) ===
    def get_rook_moves(self, rook_bitboard, friendly_pieces_bitboard, empty_squares):
        # Integer direction codes: 0=UP, 1=DOWN, 2=RIGHT, 3=LEFT
        ray_up = self.get_ray_attacks(rook_bitboard, empty_squares, 0, 0xFFFFFFFFFFFFFFFF)
        ray_down = self.get_ray_attacks(rook_bitboard, empty_squares, 1, 0xFFFFFFFFFFFFFFFF)
        ray_right = self.get_ray_attacks(rook_bitboard, empty_squares, 2, NOT_A_FILE)
        ray_left = self.get_ray_attacks(rook_bitboard, empty_squares, 3, NOT_H_FILE)

        all_rook_targets = ray_up | ray_down | ray_right | ray_left
        return (all_rook_targets & ~friendly_pieces_bitboard) & 0xFFFFFFFFFFFFFFFF

    def get_bishop_moves(self, bishop_bitboard, friendly_pieces_bitboard, empty_squares):
        # Integer direction codes: 4=UP_LEFT, 5=UP_RIGHT, 6=DOWN_LEFT, 7=DOWN_RIGHT
        ray_up_left = self.get_ray_attacks(bishop_bitboard, empty_squares, 4, NOT_H_FILE)
        ray_up_right = self.get_ray_attacks(bishop_bitboard, empty_squares, 5, NOT_A_FILE)
        ray_down_left = self.get_ray_attacks(bishop_bitboard, empty_squares, 6, NOT_H_FILE)
        ray_down_right = self.get_ray_attacks(bishop_bitboard, empty_squares, 7, NOT_A_FILE)

        all_bishop_targets = ray_up_left | ray_up_right | ray_down_left | ray_down_right
        return (all_bishop_targets & ~friendly_pieces_bitboard) & 0xFFFFFFFFFFFFFFFF

    def get_queen_moves(self, queen_bitboard, friendly_pieces_bitboard, empty_squares):
        return (self.get_rook_moves(queen_bitboard, friendly_pieces_bitboard, empty_squares) | 
                self.get_bishop_moves(queen_bitboard, friendly_pieces_bitboard, empty_squares)) & 0xFFFFFFFFFFFFFFFF

    def get_ray_attacks(self, bitboard, empty_squares, dir_code, mask):
        # Iteratively push bits in a specified integer direction until hitting a blocker
        attacks = 0
        prop = bitboard

        for _ in range(7):
            if dir_code == 2:    prop = (prop << 1) & mask & 0xFFFFFFFFFFFFFFFF # RIGHT
            elif dir_code == 3:  prop = (prop >> 1) & mask                      # LEFT
            elif dir_code == 0:  prop = (prop >> 8) & mask                      # UP
            elif dir_code == 1:  prop = (prop << 8) & mask & 0xFFFFFFFFFFFFFFFF # DOWN
            elif dir_code == 4:  prop = (prop >> 9) & mask                      # UP_LEFT
            elif dir_code == 5:  prop = (prop >> 7) & mask                      # UP_RIGHT
            elif dir_code == 6:  prop = (prop << 7) & mask & 0xFFFFFFFFFFFFFFFF # DOWN_LEFT
            elif dir_code == 7:  prop = (prop << 9) & mask & 0xFFFFFFFFFFFFFFFF # DOWN_RIGHT

            attacks |= prop
            prop &= empty_squares

        return attacks

    # === 7. DEBUG UTILITIES ===
    def print_bitboard(self, bitboard):
        # Helper method to visualize a 64-bit integer as an 8x8 grid
        print("-" * 19)
        for row in range(8):
            row_str = "| "
            for col in range(8):
                if self.check_square(bitboard, row * 8 + col):
                    row_str += "1 "
                else:
                    row_str += ". "
            print(row_str + "|")
        print("-" * 19)