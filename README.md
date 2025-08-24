# Chess Analysis AI (Top & Brilliant Move Detector)

A Python project that analyzes chess games (PGN input) using Stockfish and labels each move as Top, Excellent, Good, Mistake, Blunder, and optionally flags "Brilliant (!!)" moves based on heuristics.

## 🚀 **Status: FULLY OPERATIONAL**

✅ **All tests passing (33/33)**  
✅ **Stockfish integration working**  
✅ **CLI interface functional**  
✅ **FastAPI endpoints ready**  
✅ **Real game analysis successful**  
✅ **Repository optimized (100% Python)**  
✅ **Clean structure with minimal dependencies**

## Features

- **Move Assessment**: Labels moves as Top (≤20 cp), Excellent (≤50 cp), Good (≤120 cp), Mistake (≤300 cp), Blunder (>300 cp)
- **Brilliant Move Detection**: Identifies brilliant moves based on sacrifice, only-move, and surprise heuristics
- **Multi-depth Analysis**: Performs both shallow (depth=10) and deep (depth=20) analysis
- **MultiPV Support**: Analyzes top 3+ candidate moves
- **PGN Annotation**: Adds comments and NAGs to PGN files
- **CLI Interface**: Command-line tool for analysis
- **FastAPI Endpoint**: REST API for programmatic access

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Stockfish chess engine

### 1. Download Stockfish
Download Stockfish from [stockfishchess.org](https://stockfishchess.org/download/) and place the executable in your project directory.

**Note**: This repository includes a pre-compiled Stockfish executable for Windows (x86-64) in the `stockfish/` directory. For other platforms, download the appropriate version from the official website.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Installation
```bash
python run_tests.py
```

## Usage

### CLI Usage

```bash
python scripts/analyze.py --pgn input.pgn --engine /path/to/stockfish --output analyzed.pgn
```

Options:
- `--pgn`: Input PGN file path
- `--engine`: Path to Stockfish executable
- `--output`: Output PGN file path
- `--shallow-depth`: Shallow analysis depth (default: 10)
- `--deep-depth`: Deep analysis depth (default: 20)
- `--multipv`: Number of top moves to analyze (default: 3)

### API Usage

Start the server:
```bash
uvicorn chess_analyzer.api:app --reload
```

Analyze a game:
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"pgn": "1. e4 e5 2. Nf3 Nc6...", "engine_path": "/path/to/stockfish"}'
```

## 🏗️ Project Structure

```
chess-analyzer/
├── chess_analyzer/          # Core Python package
│   ├── __init__.py          # Package initialization
│   ├── engine.py            # Stockfish wrapper
│   ├── evaluator.py         # Move assessment logic
│   ├── annotator.py         # PGN annotation
│   ├── models.py            # Data structures
│   └── api.py               # FastAPI endpoints
├── scripts/                 # Command-line tools
│   └── analyze.py           # CLI entry point
├── tests/                   # Comprehensive test suite
├── examples/                # Sample games and usage examples
├── stockfish/               # Stockfish engine (executable only)
│   └── stockfish-windows-x86-64-avx2.exe  # Pre-compiled for Windows
├── requirements.txt         # Python dependencies
├── README.md               # This documentation
└── QUICKSTART.md           # Quick start guide
```

**Note**: The repository includes a pre-compiled Stockfish executable for Windows. For other platforms, download Stockfish from [stockfishchess.org](https://stockfishchess.org/download/).

## Move Assessment Logic

### Centipawn Loss Thresholds
- **Top**: ≤20 cp loss
- **Excellent**: ≤50 cp loss
- **Good**: ≤120 cp loss
- **Mistake**: ≤300 cp loss
- **Blunder**: >300 cp loss

### Brilliant Move Detection
A move is marked as "Brilliant (!!)" if:
1. Near-best (≤30 cp loss vs best OR equal to best)
2. AND (sacrifice OR only-move OR surprise)
3. AND eval before wasn't already winning (> +600 cp)

### Heuristics
- **Only Move**: Only legal move that keeps eval above -200 cp
- **Sacrifice**: Material drop ≥300 (pawn units) but eval doesn't collapse
- **Surprise**: Not in shallow top-N but best at deep analysis

## Output

### Annotated PGN
- Comments: `!! Brilliant`, `[Only move]`, `Δcp=+50`
- NAGs: Standard chess annotation symbols

### JSON Summary
```json
{
  "move": "e4",
  "label": "Top",
  "brilliant": true,
  "cp_gain": 30,
  "loss_vs_best": 0,
  "best_move": "e4"
}
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
The project follows PEP 8 guidelines and uses type hints throughout.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Future Features

- Web dashboard (React + FastAPI backend)
- Batch analysis of thousands of Lichess PGNs
- Export statistics (brilliant moves per player)
- ML model training on Stockfish-labeled data
