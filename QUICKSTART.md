# Chess Analysis AI - Quick Start Guide

Get up and running with Chess Analysis AI in minutes!

## Prerequisites

- Python 3.10 or higher
- Stockfish chess engine (download from [stockfishchess.org](https://stockfishchess.org/download/))

## Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd chess-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download Stockfish**
   - Visit [Stockfish Downloads](https://stockfishchess.org/download/)
   - Download the appropriate version for your OS
   - Extract and note the path to the Stockfish executable

## Quick Test

1. **Run the example script**
   ```bash
   python examples/example_usage.py
   ```

2. **Run tests**
   ```bash
   python run_tests.py
   ```

## Basic Usage

### Command Line Interface

**Analyze a single game:**
```bash
python scripts/analyze.py --pgn examples/sample_game.pgn --engine /path/to/stockfish
```

**With custom parameters:**
```bash
python scripts/analyze.py \
  --pgn examples/sample_game.pgn \
  --engine /path/to/stockfish \
  --shallow-depth 15 \
  --deep-depth 25 \
  --multipv 5 \
  --output analyzed_game.pgn
```

**Quick analysis:**
```bash
python scripts/analyze.py quick-analyze \
  --pgn examples/sample_game.pgn \
  --engine /path/to/stockfish \
  --depth 20
```

### API Usage

1. **Start the server:**
   ```bash
   uvicorn chess_analyzer.api:app --reload
   ```

2. **Analyze a game:**
   ```bash
   curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "pgn": "1. e4 e5 2. Nf3 Nc6",
       "engine_path": "/path/to/stockfish"
     }'
   ```

3. **View API documentation:**
   - Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser

## Sample Output

### Move Analysis
```
 1. W e4     [Top]      Δcp=+30                    !!
 2. B e5     [Excellent] Δcp=-20 (-50cp)           
 3. W Nf3    [Top]      Δcp=+25                    !!
```

### Summary
```
Game Analysis Summary
================================================================================
Total Moves: 26
Brilliant Moves: 3

Move Quality Distribution:
  Top: 8 (30.8%)
  Excellent: 12 (46.2%)
  Good: 4 (15.4%)
  Mistake: 2 (7.7%)
  Blunder: 0 (0.0%)
```

## Configuration

Edit `config.py` to customize:
- Analysis depths
- Move quality thresholds
- Brilliant move detection parameters
- API settings

## Troubleshooting

### Common Issues

1. **"Engine not found" error**
   - Verify Stockfish path is correct
   - Ensure Stockfish is executable
   - Try using absolute path

2. **Import errors**
   - Ensure you're in the project directory
   - Check Python version (3.10+)
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **PGN parsing errors**
   - Verify PGN file format is valid
   - Check file encoding (should be UTF-8)

### Getting Help

- Check the full [README.md](README.md) for detailed documentation
- Run `python examples/example_usage.py` to see usage examples
- Use `--help` flag with CLI commands for options

## Next Steps

- Analyze your own PGN files
- Customize analysis parameters
- Integrate with your chess applications
- Explore the API endpoints
- Run batch analysis on multiple games

## Examples Directory

The `examples/` directory contains:
- `sample_game.pgn` - Sample chess game for testing
- `example_usage.py` - Complete usage examples

Happy analyzing! 🎯♟️
