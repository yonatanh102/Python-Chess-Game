import tkinter as tk
import random

class StartMenu:
    def __init__(self, root, on_start_callback):
        self.root = root
        self.on_start_callback = on_start_callback

        self.root.title("Chess Setup")
        self.root.geometry("350x450")
        self.root.configure(padx=20, pady=20)

        self.mode_var = tk.StringVar(value="Bot")
        self.diff_var = tk.IntVar(value=3)
        self.timer_var = tk.BooleanVar(value=True)
        self.color_var = tk.StringVar(value="white")

        tk.Label(root, text="Python Chess Engine", font=("Arial", 18, "bold")).pack(pady=(0, 20))

        # --- Game Mode ---
        tk.Label(root, text="Game Mode:", font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Radiobutton(root, text="Player vs AI", variable=self.mode_var, value="Bot",command=self.toggle_bot_options).pack(anchor="w")
        tk.Radiobutton(root, text="Player vs Player", variable=self.mode_var, value="PvP", command=self.toggle_bot_options).pack(anchor="w")

        # --- Bot Level ---
        self.diff_frame = tk.Frame(root)
        self.diff_frame.pack(anchor="w", pady=(10, 0), padx=20)
        tk.Label(self.diff_frame, text="AI Depth (Difficulty):").pack(side=tk.LEFT)
        tk.OptionMenu(self.diff_frame, self.diff_var, 1, 2, 3, 4).pack(side=tk.LEFT, padx=10)

        # --- Player Color ---
        self.color_frame = tk.Frame(root)
        self.color_frame.pack(anchor="w", pady=(10, 0), padx=20)
        tk.Label(self.color_frame, text="Play as:").pack(side=tk.LEFT)
        tk.OptionMenu(self.color_frame, self.color_var, "White", "Black", "Random").pack(side=tk.LEFT, padx=10)

        # --- Timer Options ---
        tk.Label(root, text="Settings:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 5))
        tk.Checkbutton(root, text="Enable Timer (10 min)", variable=self.timer_var).pack(anchor="w")

        # --- Start Button ---
        tk.Button(root, text="Start Game", font=("Arial", 14, "bold"), background="#4CAF50", fg="white", 
                  command=self.start_game).pack(pady=30, fill=tk.X)

    def toggle_bot_options(self):
        state = tk.NORMAL if self.mode_var.get() == "Bot" else tk.DISABLED
        for child in self.diff_frame.winfo_children():
            child.configure(state=state)
        for child in self.color_frame.winfo_children():
            child.configure(state=state)

    def start_game(self):
        vs_bot = self.mode_var.get() == "Bot"
        difficulty = self.diff_var.get()
        use_timer = self.timer_var.get()
        player_color = self.color_var.get().lower()
        if player_color == "random":
            player_color = random.choice(["white", "black"])

        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.geometry("")
        
        self.on_start_callback(vs_bot, difficulty, use_timer, player_color)