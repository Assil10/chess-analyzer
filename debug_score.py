#!/usr/bin/env python3
"""
Debug script to test score handling.
"""

import chess
import chess.engine
import tempfile
import os

def test_score_handling():
    """Test how scores are handled."""
    print("Testing score handling...")
    
    # Create a simple position
    board = chess.Board()
    
    # Try to analyze with Stockfish
    stockfish_path = "stockfish/stockfish-windows-x86-64-avx2.exe"
    
    if not os.path.exists(stockfish_path):
        print(f"Stockfish not found at {stockfish_path}")
        return
    
    try:
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            print("Connected to Stockfish")
            
            # Analyze position
            result = engine.analyse(board, chess.engine.Limit(depth=5))
            print(f"Analysis result type: {type(result)}")
            print(f"Result keys: {result.keys()}")
            
            if "score" in result:
                score = result["score"]
                print(f"Score type: {type(score)}")
                print(f"Score dir: {[m for m in dir(score) if not m.startswith('_')]}")
                
                if hasattr(score, 'white'):
                    print(f"Score.white type: {type(score.white)}")
                    white_score = score.white()
                    print(f"White score type: {type(white_score)}")
                    print(f"White score dir: {[m for m in dir(white_score) if not m.startswith('_')]}")
                    
                    if hasattr(white_score, 'score'):
                        print(f"white_score.score is callable: {callable(white_score.score)}")
                        try:
                            cp_score = white_score.score(mate_score=10000)
                            print(f"Centipawn score: {cp_score}")
                        except Exception as e:
                            print(f"Error calling white_score.score(): {e}")
                    
                    if hasattr(white_score, 'mate'):
                        print(f"white_score.mate is callable: {callable(white_score.mate)}")
                        try:
                            mate_value = white_score.mate()
                            print(f"Mate value: {mate_value}")
                        except Exception as e:
                            print(f"Error calling white_score.mate(): {e}")
                
                if hasattr(score, 'score'):
                    print(f"score.score is callable: {callable(score.score)}")
                    try:
                        cp_score = score.score()
                        print(f"Direct score: {cp_score}")
                    except Exception as e:
                        print(f"Error calling score.score(): {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_score_handling()
