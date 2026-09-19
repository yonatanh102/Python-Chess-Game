
import tkinter as tk
import tkinter.messagebox as messagebox
from Game import Game
from AI import get_best_move
from StartMenu import StartMenu
import threading
import copy

# === 1. CONSTANTS & CONFIGURATION ===
BOARD_SIZE = 600
SQUARE_SIZE = BOARD_SIZE // 8

# Colors
LIGHT_COLOR = "#F0D9B5"
DARK_COLOR = "#B58863"
HIGHLIGHT_COLOR = "#7B68EE"
HINT_COLOR = "#A9A9A9"
CAPTURE_COLOR = "#FF6347"

# Margins for coordinate labels
MARGIN_LEFT = 40
MARGIN_BOTTOM = 40
MARGIN_TOP = 20
MARGIN_RIGHT = 20

# Unicode piece mapping
PIECE_SYMBOLS = {
    "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟", 
    "r": "♜", "n": "♞", "b": "♝", "q": "♛", "k": "♚", "p": "♟"  
}


class ChessGUI:
    
    # === 2. INITIALIZATION & UI SETUP ===
    def __init__(self, root, vs_bot=True, bot_difficulty=3, use_timer=True, player_color="white"):
        self.root = root
        self.root.title("Python Chess Engine")
        
        # Game State
        self.game = Game()
        self.selected_square = None
        self.ai_thinking = False

        # Match Settings
        self.vs_bot = vs_bot
        self.bot_difficulty = bot_difficulty
        self.use_timer = use_timer
        self.player_color = player_color
        self.ai_color = "white" if self.player_color == "black" else "black"
        
        # Timer State
        self.white_time = 10 * 60 
        self.black_time = 10 * 60
        self.timer_running = self.use_timer

        self._build_ui()

        if self.use_timer:
            self.update_timer() 
        else:
            self.white_timer_label.configure(text="White: inf")
            self.black_timer_label.configure(text="Black: inf")

    def _build_ui(self):
        """ Constructs the frames, labels, buttons, and the main drawing canvas. """
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10)

        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))

        self.white_timer_label = tk.Label(self.control_frame, text="White: 10:00", font=("Arial", 16, "bold"), bg="white", fg="black", width=12, pady=5, relief=tk.RAISED)
        self.white_timer_label.pack(side=tk.LEFT, padx=5)

        self.turn_label = tk.Label(self.control_frame, text="Turn: White", font=("Arial", 18, "bold"))
        self.turn_label.pack(side=tk.LEFT, expand=True)

        self.black_timer_label = tk.Label(self.control_frame, text="Black: 10:00", font=("Arial", 16, "bold"), bg="black", fg="white", width=12, pady=5, relief=tk.RAISED)
        self.black_timer_label.pack(side=tk.LEFT, padx=5)

        self.undo_button = tk.Button(self.control_frame, text="Undo ⟲", font=("Arial", 14, "bold"), command=self.on_undo, bg="#e0e0e0", cursor="hand2")
        self.undo_button.pack(side=tk.RIGHT, padx=10)

        canvas_width = BOARD_SIZE + MARGIN_LEFT + MARGIN_RIGHT
        canvas_height = BOARD_SIZE + MARGIN_TOP + MARGIN_BOTTOM
        self.canvas = tk.Canvas(self.main_frame, width=canvas_width, height=canvas_height)
        self.canvas.pack(side=tk.BOTTOM)
        self.canvas.bind("<Button-1>", self.on_square_clicked)

        self.draw_board()


    # === 3. TIMER MANAGEMENT ===
    def format_time(self, seconds):
        """ Converts raw seconds into MM:SS format. """
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def update_timer(self):
        """ Recursive loop that decrements the active player's clock every second. """
        if not self.timer_running:
            return

        if self.game.turn == "white":
            self.white_time -= 1
        else:
            self.black_time -= 1

        self.white_timer_label.config(text=f"White: {self.format_time(self.white_time)}")
        self.black_timer_label.config(text=f"Black: {self.format_time(self.black_time)}")

        if self.white_time <= 0 or self.black_time <= 0:
            self.timer_running = False
            winner = "Black" if self.white_time <= 0 else "White"
            messagebox.showinfo("Time's Up!", f"{winner} wins on time!")
            return

        # Schedule the next tick
        self.root.after(1000, self.update_timer)


    # === 4. PLAYER INTERACTION ===
    def update_turn_label(self):
        self.turn_label.config(text=f"Turn: {self.game.turn.capitalize()}")

    def on_undo(self):
        """ Reverts the last board state. Disabled while the AI is thinking. """
        if getattr(self, 'ai_thinking', False):
            return
        
        if self.game.move_history:
            self.game.undo_move()
            self.game.switch_turn()
            self.selected_square = None
            self.update_turn_label()
            self.draw_board()

    def on_square_clicked(self, event):
        """ Handles mouse clicks, selection logic, and triggers moves. """
        if self.use_timer and not self.timer_running:
            return

        # Prevent player from interacting during AI turn
        if self.vs_bot and self.game.turn == self.ai_color:
            print("Please wait, the AI is thinking")
            return
            
        x_click = event.x - MARGIN_LEFT
        y_click = event.y - MARGIN_TOP
        
        # Ignore clicks outside the grid
        if x_click < 0 or x_click >= BOARD_SIZE or y_click < 0 or y_click >= BOARD_SIZE:
            return 

        col = x_click // SQUARE_SIZE
        row = y_click // SQUARE_SIZE
        clicked_pos = (row, col)

        if self.selected_square is None:
            # Select a piece
            piece = self.game.board.get_piece(row, col)
            if piece and piece.color == self.game.turn:
                self.selected_square = clicked_pos
        else:
            # Change selection or execute move
            if clicked_pos == self.selected_square:
                self.selected_square = None
            elif self.game.board.get_square(row, col).has_team_piece(self.game.turn):
                self.selected_square = clicked_pos
            else:
                success = self.game.move_piece(self.selected_square, clicked_pos)
                if success:
                    self.selected_square = None
                    self.update_turn_label()
                    self.draw_board()

                    game_status = self.game.check_game_over()
                    if game_status:
                        self.timer_running = False
                        messagebox.showinfo("Game Over", game_status)
                    elif self.vs_bot and self.game.turn == self.ai_color:
                        self.root.after(100, self.make_ai_move)

        self.draw_board()


    # === 5. AI INTEGRATION (Threading) ===
    def make_ai_move(self):
        """ 
        Initiates the AI calculation in a separate background thread 
        to prevent freezing the main GUI event loop. 
        """
        if (self.use_timer and not self.timer_running) or not self.vs_bot or self.game.turn != self.ai_color:
            return
            
        print(f"AI {self.ai_color} is thinking at depth {self.bot_difficulty}...")
        self.ai_thinking = True
        self.undo_button.config(state=tk.DISABLED)

        def calculate_and_move():
            try:
                # Deepcopy the game state so the AI can simulate moves without mutating the visible board
                memo = {id(self.game.bb_engine): self.game.bb_engine}
                game_copy = copy.deepcopy(self.game, memo)
                best_move = get_best_move(game_copy, depth=self.bot_difficulty, ai_color=self.ai_color)
            except Exception as e:
                print(f"AI calculation failed: {e}")
                best_move = None
            finally:
                # Schedule the UI update back on the main thread
                self.root.after(0, self.apply_ai_move, best_move)

        threading.Thread(target=calculate_and_move, daemon=True).start()

    def apply_ai_move(self, best_move):
        """ Executes the AI's chosen move on the main thread and updates the UI. """
        self.ai_thinking = False
        self.undo_button.config(state=tk.NORMAL)

        if best_move:
            start, end = best_move
            self.game.make_move(start, end)
            self.game.switch_turn()

            self.draw_board()
            self.update_turn_label()

            game_status = self.game.check_game_over()
            if game_status:
                self.timer_running = False
                messagebox.showinfo("Game Over", game_status)


    # === 6. RENDERING ===
    def draw_board(self):
        """ Clears the canvas and redraws the board, coordinates, hints, and pieces. """
        self.canvas.delete("all")

        # Fetch legal moves for the selected piece to draw hints
        valid_moves = []
        if self.selected_square:
            row, col = self.selected_square
            piece = self.game.board.get_piece(row, col)
            if piece and piece.color == self.game.turn:
                valid_moves = self.game.get_legal_moves(piece)

        for row in range(8):
            # Draw row numbers (1-8)
            num = str(8 - row)
            y_center = MARGIN_TOP + row * SQUARE_SIZE + (SQUARE_SIZE // 2)
            self.canvas.create_text(MARGIN_LEFT // 2, y_center, text=num, font=("Arial", 16, "bold"), fill="black")

            for col in range(8):
                # Draw column letters (A-H)
                if row == 7:
                    letter = chr(ord('A') + col)
                    x_center = MARGIN_LEFT + col * SQUARE_SIZE + (SQUARE_SIZE // 2)
                    self.canvas.create_text(x_center, MARGIN_TOP + BOARD_SIZE + (MARGIN_BOTTOM // 2), text=letter, font=("Arial", 16, "bold"), fill="black")

                # Square dimensions
                x1 = MARGIN_LEFT + col * SQUARE_SIZE
                y1 = MARGIN_TOP + row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                # Base square color
                color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
                if self.selected_square == (row, col):
                    color = HIGHLIGHT_COLOR

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                # Draw move hints (circles)
                if (row, col) in valid_moves:
                    target_square = self.game.board.get_square(row, col)
                    radius = SQUARE_SIZE // 6
                    hint_fill = HINT_COLOR
                    
                    if not target_square.is_empty:
                        hint_fill = CAPTURE_COLOR
                        radius = SQUARE_SIZE // 2.5

                    cx, cy = x1 + SQUARE_SIZE // 2, y1 + SQUARE_SIZE // 2
                    self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=hint_fill, outline="")

                # Draw pieces
                piece = self.game.board.get_piece(row, col)
                if piece:
                    symbol = PIECE_SYMBOLS.get(str(piece), "?")
                    text_color = "black" if piece.color == "black" else "white"

                    self.canvas.create_text(
                        x1 + SQUARE_SIZE // 2,
                        y1 + SQUARE_SIZE // 2,
                        text=symbol,
                        font=("Arial", 32),
                        fill=text_color)


if __name__ == "__main__":
    root = tk.Tk()

    def launch_game(vs_bot, bot_difficulty, use_timer, player_color):
        app = ChessGUI(root, vs_bot, bot_difficulty, use_timer, player_color)
        if vs_bot and player_color == "black":
            root.after(200, app.make_ai_move)

    menu = StartMenu(root, launch_game)
    root.mainloop()