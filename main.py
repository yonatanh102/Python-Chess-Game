
from Game import Game

# === 1. UTILITIES ===
def print_board_with_moves(board, moves_list=None):
    """
    Helper function to print the board to the console.
    Highlights valid moves with an 'X' if a moves_list is provided.
    """
    display_grid = []

    for r in range(8):
        row_str = []
        for c in range(8):
            piece = board.get_piece(r, c)
            symbol = str(piece) if piece else "."

            # Highlight valid moves
            if moves_list and (r, c) in moves_list:
                symbol = "X"

            row_str.append(symbol)
        display_grid.append(row_str)

    print("   0 1 2 3 4 5 6 7")  
    print("  -----------------")
    for i, row in enumerate(display_grid):
        print(f"{i} | {' '.join(row)} |")
    print("  -----------------")

def parse_input(input_str):
    """
    Converts string input like '6,4' into a tuple (6, 4).
    Returns None if the format is invalid.
    """
    try:
        r, c = input_str.split(',')
        return int(r), int(c)
    except ValueError:
        return None

# === 2. MAIN LOOP ===
def main():
    """
    Entry point for the text-based command-line interface.
    """
    game = Game()

    print("Welcome to Python Chess (Text Version)!")
    print("Format: row,col (e.g., '6,4' to select, then '4,4' to move)")
    print("Type 'exit' at any time to quit.")

    running = True
    while running:
        print("\n" + "=" * 20)
        print_board_with_moves(game.board)
        
        print(f"Current Turn: {game.turn.upper()}")

        # 1. Piece Selection
        start_str = input("Select piece (row,col): ")
        if start_str.lower() == 'exit': 
            break

        start_pos = parse_input(start_str)
        if not start_pos:
            print("Invalid format. Try again.")
            continue

        # Show valid moves for the selected piece
        piece = game.board.get_piece(start_pos[0], start_pos[1])
        if piece and piece.color == game.turn:
            valid_moves = game.get_legal_moves(piece)
            print_board_with_moves(game.board, valid_moves)
        else:
            print("Not your piece or empty square.")
            continue

        # 2. Target Selection
        end_str = input("Move to (row,col): ")
        if end_str.lower() == 'exit': 
            break

        end_pos = parse_input(end_str)
        if not end_pos:
            print("Invalid format. Try again.")
            continue

        # 3. Execution
        success = game.move_piece(start_pos, end_pos)

        if success:
            print("Move successful!")
            status = game.check_game_over()
            if status:
                print(status)
                break
        else:
            print("Illegal move. Try again.")

if __name__ == "__main__":
    main()