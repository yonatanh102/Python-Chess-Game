
# === 1. GLOBAL MASKS (Edge Wrapping Prevention) ===
# These constants prevent pieces from "teleporting" across the board boundaries 
# during bitwise shifts. 0s are placed on the restricted edges.
cdef unsigned long long NOT_A_FILE = 0xFEFEFEFEFEFEFEFE
cdef unsigned long long NOT_H_FILE = 0x7F7F7F7F7F7F7F7F
cdef unsigned long long NOT_AB_FILE = 0xFCFCFCFCFCFCFCFC
cdef unsigned long long NOT_GH_FILE = 0x3F3F3F3F3F3F3F3F

cdef class BitboardEngine:

    # State variables storing piece positions as 64-bit integers
    cdef public unsigned long long black_rooks, black_knights, black_bishops, black_queens, black_king, black_pawns
    cdef public unsigned long long white_pawns, white_rooks, white_knights, white_bishops, white_queens, white_king

    # === 2. INITIALIZATION ===
    def __init__(self):
        # Initialize standard chess starting positions using hexadecimal bitmasks
        
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
    cpdef unsigned long long set_piece(self, unsigned long long bitboard, int square_index):
        # Turn ON a specific bit using OR
        return bitboard | (1ULL << square_index)

    cpdef unsigned long long clear_piece(self, unsigned long long bitboard, int square_index):
        # Turn OFF a specific bit using AND with NOT
        return bitboard & ~(1ULL << square_index)

    cpdef bint check_square(self, unsigned long long bitboard, int square_index):
        # Check if a specific bit is 1
        return (bitboard & (1ULL << square_index)) != 0

    cpdef int get_index(self, int row, int col):
        return row * 8 + col

    cpdef tuple get_coords(self, int index):
        return index // 8, index % 8

    cpdef list get_coords_list(self, unsigned long long bitboard):
        # Scan all 64 bits and return a list of (row, col) tuples for active bits
        cdef list coords = []
        cdef int i
        for i in range(64):
            if (bitboard & (1ULL << i)) != 0:
                coords.append((i // 8, i % 8))
        return coords

    # === 4. BOARD STATE AGGREGATORS ===
    cpdef unsigned long long get_all_white_pieces(self):
        return (self.white_pawns | self.white_bishops | self.white_king | 
                self.white_knights | self.white_queens | self.white_rooks)

    cpdef unsigned long long get_all_black_pieces(self):
        return (self.black_pawns | self.black_bishops | self.black_king | 
                self.black_knights | self.black_queens | self.black_rooks)

    cpdef unsigned long long get_occupied_squares(self):
        return self.get_all_white_pieces() | self.get_all_black_pieces()

    # === 5. LEAPING PIECE MOVE GENERATORS (O(1) operations) ===
    
    cpdef unsigned long long get_white_pawn_moves(self, unsigned long long pawns_bitboard, unsigned long long empty_squares, unsigned long long enemy_pieces):
        # Shift 8 bits right for a single push UP
        cdef unsigned long long single_pushes = (pawns_bitboard >> 8) & empty_squares
        # Shift the valid single pushes another 8 bits right for a double push
        cdef unsigned long long double_pushes = (single_pushes >> 8) & empty_squares & 0x000000FF00000000
        
        # Diagonal attacks (shift 9 and 7) masked against edge wrapping and enemy pieces
        cdef unsigned long long attack_left = (pawns_bitboard >> 9) & NOT_H_FILE & enemy_pieces
        cdef unsigned long long attack_right = (pawns_bitboard >> 7) & NOT_A_FILE & enemy_pieces
        
        return (single_pushes | double_pushes | attack_left | attack_right) & 0xFFFFFFFFFFFFFFFF

    cpdef unsigned long long get_black_pawn_moves(self, unsigned long long pawns_bitboard, unsigned long long empty_squares, unsigned long long enemy_pieces):
        # Black pawns move DOWN the board (shift left instead of right)
        cdef unsigned long long single_pushes = (pawns_bitboard << 8) & empty_squares
        cdef unsigned long long double_pushes = (single_pushes << 8) & empty_squares & 0x00000000FF000000
        
        cdef unsigned long long attack_left = (pawns_bitboard << 7) & NOT_H_FILE & enemy_pieces
        cdef unsigned long long attack_right = (pawns_bitboard << 9) & NOT_A_FILE & enemy_pieces
        
        return (single_pushes | double_pushes | attack_left | attack_right) & 0xFFFFFFFFFFFFFFFF

    cpdef unsigned long long get_king_moves(self, unsigned long long king_bitboard, unsigned long long friendly_pieces_bitboard):
        # Calculate all 8 adjacent squares by shifting
        cdef unsigned long long step_up = king_bitboard >> 8
        cdef unsigned long long step_down = king_bitboard << 8
        cdef unsigned long long step_left = (king_bitboard >> 1) & NOT_H_FILE
        cdef unsigned long long step_right = (king_bitboard << 1) & NOT_A_FILE
        cdef unsigned long long step_up_right = (king_bitboard >> 7) & NOT_A_FILE
        cdef unsigned long long step_up_left = (king_bitboard >> 9) & NOT_H_FILE
        cdef unsigned long long step_down_right = (king_bitboard << 9) & NOT_A_FILE
        cdef unsigned long long step_down_left = (king_bitboard << 7) & NOT_H_FILE

        cdef unsigned long long all_king_targets = (step_down | step_left | step_right | step_up | 
                                                    step_up_right | step_down_left | step_down_right | step_up_left)

        # Exclude squares occupied by friendly pieces
        return (all_king_targets & ~friendly_pieces_bitboard) & 0xFFFFFFFFFFFFFFFF

    cpdef unsigned long long get_knight_moves(self, unsigned long long knight_bitboard, unsigned long long friendly_pieces_bitboard):
        # L-shapes calculated by combining vertical and horizontal shifts
        cdef unsigned long long up_up_left = (knight_bitboard >> 17) & NOT_H_FILE
        cdef unsigned long long up_up_right = (knight_bitboard >> 15) & NOT_A_FILE
        cdef unsigned long long up_left_left = (knight_bitboard >> 10) & NOT_GH_FILE
        cdef unsigned long long up_right_right = (knight_bitboard >> 6) & NOT_AB_FILE
        cdef unsigned long long down_down_left = (knight_bitboard << 15) & NOT_H_FILE
        cdef unsigned long long down_down_right = (knight_bitboard << 17) & NOT_A_FILE
        cdef unsigned long long down_left_left = (knight_bitboard << 6) & NOT_GH_FILE
        cdef unsigned long long down_right_right = (knight_bitboard << 10) & NOT_AB_FILE

        cdef unsigned long long all_knights_targets = (up_up_left | up_up_right | up_left_left | up_right_right |
                                                       down_down_left| down_down_right | down_left_left | down_right_right)

        return (all_knights_targets & ~friendly_pieces_bitboard) & 0xFFFFFFFFFFFFFFFF

    # === 6. SLIDING PIECE MOVE GENERATORS (Ray Casting) ===

    cpdef unsigned long long get_ray_attacks(self, unsigned long long bitboard, unsigned long long empty_squares, int dir_code, unsigned long long mask):
        # Iteratively push the bits in a specific direction until they hit a blocker (edge or piece)
        cdef unsigned long long attacks = 0
        cdef unsigned long long prop = bitboard
        cdef int _

        # Max sliding distance on a chessboard is 7 squares
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
            prop &= empty_squares # Stop propagating if the square is not empty

        return attacks

    cpdef unsigned long long get_rook_moves(self, unsigned long long rook_bitboard, unsigned long long friendly_pieces_bitboard, unsigned long long empty_squares):
        # Generate moves for straight lines (Up, Down, Right, Left)
        cdef unsigned long long ray_up = self.get_ray_attacks(rook_bitboard, empty_squares, 0, 0xFFFFFFFFFFFFFFFF)
        cdef unsigned long long ray_down = self.get_ray_attacks(rook_bitboard, empty_squares, 1, 0xFFFFFFFFFFFFFFFF)
        cdef unsigned long long ray_right = self.get_ray_attacks(rook_bitboard, empty_squares, 2, NOT_A_FILE)
        cdef unsigned long long ray_left = self.get_ray_attacks(rook_bitboard, empty_squares, 3, NOT_H_FILE)

        cdef unsigned long long all_rook_targets = ray_up | ray_down | ray_right | ray_left
        return (all_rook_targets & ~friendly_pieces_bitboard) & 0xFFFFFFFFFFFFFFFF

    cpdef unsigned long long get_bishop_moves(self, unsigned long long bishop_bitboard, unsigned long long friendly_pieces_bitboard, unsigned long long empty_squares):
        # Generate moves for diagonal lines
        cdef unsigned long long ray_up_left = self.get_ray_attacks(bishop_bitboard, empty_squares, 4, NOT_H_FILE)
        cdef unsigned long long ray_up_right = self.get_ray_attacks(bishop_bitboard, empty_squares, 5, NOT_A_FILE)
        cdef unsigned long long ray_down_left = self.get_ray_attacks(bishop_bitboard, empty_squares, 6, NOT_H_FILE)
        cdef unsigned long long ray_down_right = self.get_ray_attacks(bishop_bitboard, empty_squares, 7, NOT_A_FILE)

        cdef unsigned long long all_bishop_targets = ray_up_left | ray_up_right | ray_down_left | ray_down_right
        return (all_bishop_targets & ~friendly_pieces_bitboard) & 0xFFFFFFFFFFFFFFFF

    cpdef unsigned long long get_queen_moves(self, unsigned long long queen_bitboard, unsigned long long friendly_pieces_bitboard, unsigned long long empty_squares):
        # A Queen is simply a combination of a Rook and a Bishop
        return (self.get_rook_moves(queen_bitboard, friendly_pieces_bitboard, empty_squares) | 
                self.get_bishop_moves(queen_bitboard, friendly_pieces_bitboard, empty_squares)) & 0xFFFFFFFFFFFFFFFF

    # === 7. DEBUG UTILITIES ===
    def print_bitboard(self, unsigned long long bitboard):
        # Helper method to visualize the 64-bit integer as an 8x8 grid in the console
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