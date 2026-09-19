# Python Chess Engine ♟️

A fully functional, optimized chess engine built from scratch in Python and Cython. This project bridges the gap between Object-Oriented Programming (OOP) readability and low-level bitwise performance, featuring a custom GUI, a highly optimized Minimax AI, and full compliance with standard chess rules.

---

## 🚀 Features

- **Full Rule Enforcement**: Supports castling, en passant, promotion, and check/checkmate detection.
- **Technical Draws**: Accurately detects the 50-move rule, threefold repetition, and insufficient mating material.
- **Game Modes**: Play against a local opponent or challenge the AI (Depth 1-4).
- **UX/UI**: Custom Tkinter GUI with a toggleable match timer (10 minutes) and full move history Undo capabilities.

---

## 🧠 Architecture & Design Patterns

The engine relies on a hybrid architecture to maintain clean code without sacrificing search depth:

- **Strategy Pattern**: An OOP `Piece` hierarchy delegates sliding/leaping move generation to specific classes (e.g., `Rook`, `Knight`).
- **Adapter Pattern**: `Game.get_bb_pseudo_moves` seamlessly bridges the OOP game board with the Cython bitboard layer, returning standard `(row, col)` coordinates to the UI.
- **Command/Memento Pattern**: Moves are pushed to a history stack containing delta states (castling rights, en passant targets, half-move clocks), enabling flawless O(1) `undo_move` executions without duplicating the board state.

---

## ⚡ Performance Optimizations (The Bitboard Engine)

The core computational heavy lifting is completely decoupled from the OOP layer:

- **Cython Compilation**: The bitboard engine (`FastBitboard.pyx`) is compiled to C. Board states are stored as `unsigned long long` 64-bit integers, reducing move generation to single-clock bitwise operations (`<<`, `>>`, `&`, `|`).
- **Ray Casting (Dumb7Fill)**: Sliding pieces use iterative bit shifts masked against constant edge files (`NOT_A_FILE`, `NOT_H_FILE`) to prevent edge-wrapping bugs.
- **O(1) State Tracking**: King positions are tracked instantly in a dictionary, bypassing full 8x8 board scans during check detection.
- **Bit-Driven Iteration**: Move generators and the static evaluator loop strictly over active set bits (via `get_coords_list`), scaling performance with the number of remaining pieces rather than fixed grid size.

---

## 🤖 AI Search & Heuristics

- **Minimax with Alpha-Beta Pruning**: Traverses the game tree to evaluate optimal moves while pruning unviable opponent branches.
- **MVV-LVA Move Ordering**: Pre-sorts pseudo-legal moves prioritizing "Most Valuable Victim - Least Valuable Attacker" to maximize Alpha-Beta cutoff efficiency.
- **Zobrist Hashing (Transposition Table)**: Generates a unique 64-bit hash for every board state, dynamically updated via XOR operations when pieces move, castling rights change, or en passant targets expire. Cached evaluations prevent redundant subtree searches.
- **Asynchronous Execution**: The AI runs on a separate daemon thread utilizing a deep-copied engine instance (`copy.deepcopy`), ensuring the Tkinter UI remains fully responsive during deep searches.

---

## 🛠️ Tools & Technologies

| Category | Technology |
|---|---|
| **Language** | Python 3.13 |
| **UI** | Tkinter |
| **Performance** | Cython |
| **Testing** | Pytest (comprehensive suite covering bitboard math, OOP rules, draw edge cases, and AI blunder avoidance) |
| **Deployment** | Docker |

---

## 🚀 Installation & Usage

### Local Setup (Requires a C Compiler for Cython)

```bash
# 1. Install dependencies
pip install cython pytest

# 2. Compile the Cython Bitboard engine
python setup.py build_ext --inplace

# 3. Launch the graphical interface
python Gui.py
```

### Docker (Ideal for testing/CI)

```bash
docker build -t python-chess .
docker run --rm python-chess pytest
```

> **Note:** Running the Tkinter GUI via Docker requires X11 Forwarding configuration.

---

## 🔮 Future Enhancements

- **Iterative Deepening & Time Management**: Transitioning from fixed-depth searches to time-budgeted execution.
- **Quiescence Search**: Searching beyond the depth limit during active capture sequences to prevent the "horizon effect" blunder.
- **Parallel Search**: Utilizing multiple CPU cores for root-level move evaluation.
