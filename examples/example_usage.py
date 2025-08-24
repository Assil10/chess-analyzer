#!/usr/bin/env python3
"""
Example usage of the Chess Analysis AI system.

This script demonstrates how to use the chess analysis components
programmatically without the CLI or API.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chess_analyzer.engine import ChessEngine
from chess_analyzer.evaluator import MoveEvaluator
from chess_analyzer.annotator import PGNAnnotator
from chess_analyzer.models import GameAnalysis
import chess.pgn


def analyze_sample_game():
    """Analyze the sample game from PGN file."""
    
    # Path to sample game
    sample_pgn_path = Path(__file__).parent / "sample_game.pgn"
    
    if not sample_pgn_path.exists():
        print(f"Sample PGN file not found: {sample_pgn_path}")
        return
    
    # Read PGN file
    with open(sample_pgn_path, 'r') as f:
        pgn_content = f.read()
    
    print("Sample PGN content:")
    print(pgn_content)
    print("-" * 50)
    
    # Parse PGN
    pgn_io = io.StringIO(pgn_content)
    game = chess.pgn.read_game(pgn_io)
    
    if game is None:
        print("Failed to parse PGN")
        return
    
    print(f"Game parsed successfully. Moves: {len(list(game.mainline()))}")
    print("-" * 50)
    
    # Note: In a real scenario, you would need Stockfish installed
    # For this example, we'll show the structure without actual analysis
    
    print("Game Analysis Structure:")
    print(f"Event: {game.headers.get('Event', 'Unknown')}")
    print(f"White: {game.headers.get('White', 'Unknown')}")
    print(f"Black: {game.headers.get('Black', 'Unknown')}")
    print(f"Result: {game.headers.get('Result', 'Unknown')}")
    print(f"ECO: {game.headers.get('ECO', 'Unknown')}")
    
    # Show moves
    print("\nMoves:")
    board = game.board()
    move_number = 1
    
    for node in game.mainline():
        if node.move:
            san = board.san(node.move)
            print(f"{move_number}. {san}")
            board.push(node.move)
            move_number += 1
    
    print(f"\nTotal moves: {move_number - 1}")
    print("-" * 50)
    
    print("Note: To perform actual analysis, you need:")
    print("1. Stockfish engine installed")
    print("2. Path to Stockfish executable")
    print("3. Use the CLI tool: python scripts/analyze.py --pgn sample_game.pgn --engine /path/to/stockfish")


def demonstrate_models():
    """Demonstrate the data models."""
    
    print("Data Models Demonstration:")
    print("=" * 50)
    
    from chess_analyzer.models import MoveLabel, MoveAssessment, GameAnalysis
    
    # Show move labels
    print("Move Labels:")
    for label in MoveLabel:
        print(f"  {label.value}")
    
    print("\nMove Label Thresholds:")
    print("  Top: ≤20 cp loss")
    print("  Excellent: ≤50 cp loss")
    print("  Good: ≤120 cp loss")
    print("  Mistake: ≤300 cp loss")
    print("  Blunder: >300 cp loss")
    
    print("\nBrilliant Move Detection:")
    print("  - Near-best (≤30 cp loss vs best)")
    print("  - AND (sacrifice OR only-move OR surprise)")
    print("  - AND eval before wasn't already winning (> +600 cp)")
    
    print("\nHeuristics:")
    print("  - Only Move: Only legal move that keeps eval above -200 cp")
    print("  - Sacrifice: Material drop ≥300 pawn units but eval doesn't collapse")
    print("  - Surprise: Not in shallow top-N but best at deep analysis")


def demonstrate_api_usage():
    """Demonstrate API usage."""
    
    print("\nAPI Usage Demonstration:")
    print("=" * 50)
    
    print("Start the API server:")
    print("  uvicorn chess_analyzer.api:app --reload")
    
    print("\nAvailable endpoints:")
    print("  GET  / - API information")
    print("  GET  /health - Health check")
    print("  GET  /stats - API statistics")
    print("  POST /analyze - Analyze game from PGN string")
    print("  POST /analyze-file - Analyze game from uploaded file")
    print("  POST /analyze-batch - Analyze multiple games")
    
    print("\nExample API request:")
    print("  curl -X POST 'http://localhost:8000/analyze' \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{")
    print('      "pgn": "1. e4 e5 2. Nf3 Nc6",')
    print('      "engine_path": "/path/to/stockfish"')
    print("    }'")


def demonstrate_cli_usage():
    """Demonstrate CLI usage."""
    
    print("\nCLI Usage Demonstration:")
    print("=" * 50)
    
    print("Basic analysis:")
    print("  python scripts/analyze.py --pgn sample_game.pgn --engine /path/to/stockfish")
    
    print("\nWith custom parameters:")
    print("  python scripts/analyze.py \\")
    print("    --pgn sample_game.pgn \\")
    print("    --engine /path/to/stockfish \\")
    print("    --shallow-depth 15 \\")
    print("    --deep-depth 25 \\")
    print("    --multipv 5 \\")
    print("    --output analyzed_game.pgn \\")
    print("    --json-output results.json")
    
    print("\nQuick analysis:")
    print("  python scripts/analyze.py quick-analyze \\")
    print("    --pgn sample_game.pgn \\")
    print("    --engine /path/to/stockfish \\")
    print("    --depth 20")
    
    print("\nShow only summary:")
    print("  python scripts/analyze.py \\")
    print("    --pgn sample_game.pgn \\")
    print("    --engine /path/to/stockfish \\")
    print("    --summary-only")


def main():
    """Main demonstration function."""
    
    print("Chess Analysis AI - Example Usage")
    print("=" * 60)
    
    # Demonstrate data models
    demonstrate_models()
    
    # Demonstrate API usage
    demonstrate_api_usage()
    
    # Demonstrate CLI usage
    demonstrate_cli_usage()
    
    # Analyze sample game
    print("\n" + "=" * 60)
    analyze_sample_game()
    
    print("\n" + "=" * 60)
    print("For more information, see README.md")
    print("To run tests: python -m pytest tests/")
    print("To install dependencies: pip install -r requirements.txt")


if __name__ == "__main__":
    # Add missing import
    import io
    main()
