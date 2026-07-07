# ♟️ Chaturanga

**Chaturanga** is a high-performance chess engine written entirely in Python, featuring modern search optimizations, opening book support, and a full-stack web interface powered by FastAPI and React.

The engine is designed to efficiently analyze positions, calculate strong moves, and provide an interactive chess-playing experience through a web application.

---

## Features

### Engine Core

* Pure Python chess engine
* Legal move generation
* FEN position parsing
* Make/undo move architecture
* Castling support
* En passant support
* Pawn promotions
* Check, checkmate, and stalemate detection
* Threefold repetition detection
* Move legality validation

### Search & Evaluation

* Negamax search
* Alpha-Beta Pruning
* Iterative Deepening
* Quiescence Search
* Transposition Tables (TT)
* Killer Move Heuristic
* History Heuristic
* Principal Variation Search
* Best Move Iteration
* Efficient Move Ordering

### Opening Play

* Integrated opening book
* Strong opening move selection
* Reduced search overhead in known positions

### Performance

* Estimated playing strength: **~2250 Elo**
* Optimized search tree exploration
* Fast position evaluation
* Efficient board representation
* Millions of positions analyzed during testing and tuning

### Full-Stack Application

* FastAPI backend
* React frontend
* REST API for engine interaction
* Interactive chessboard interface
* Real-time move generation and analysis

---

## Tech Stack

### Backend

* Python
* FastAPI
* Uvicorn

### Frontend

* React
* JavaScript
* CSS

### Deployment

* Docker
* AWS EC2

---

## Search Architecture

The engine combines multiple classical chess-engine techniques to achieve strong playing strength and efficient search performance.

```text
Iterative Deepening
        │
        ▼
     Negamax
        │
        ▼
 Alpha-Beta Pruning
        │
 ┌──────┼──────┐
 ▼      ▼      ▼
TT    Killer  History
Lookup Moves  Heuristic
        │
        ▼
 Quiescence Search
        │
        ▼
   Best Move
```

---

## Engine Strength

Current estimated strength:

**≈ 2250 Elo**

Strength estimation is based on self-play testing, engine matches, and practical gameplay evaluation. Actual performance may vary depending on hardware, time controls, and testing methodology.

---

## API Example

### Request

```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

### Response

```json
{
  "best_move": "e2e4",
  "evaluation": 0.32,
  "depth": 10
}
```

---

## Running Locally

### Backend

```bash
git clone https://github.com/aks3434/Chaturanga-Python-chess-engine-.git
cd Chaturanga-Python-chess-engine-

pip install -r requirements.txt
uvicorn main:app --reload
```

Backend will be available at:

```text
http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at:

```text
http://localhost:3000
```

---

## Future Improvements

* Endgame tablebases
* NNUE-style evaluation
* Multi-threaded search
* Time management system
* UCI protocol support
* Engine-vs-engine tournament framework
* PGN import/export
* Advanced analysis mode

---

## Project Goals

Chaturanga was built as a deep dive into:

* Game-tree search algorithms
* Artificial intelligence techniques
* Performance optimization
* Backend API development
* Full-stack application deployment
* Chess engine architecture

The project demonstrates how classical AI search methods can be combined with modern software engineering practices to create a competitive chess engine entirely in Python.

---

## License

This project is released under the MIT License.
