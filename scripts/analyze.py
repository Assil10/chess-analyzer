#!/usr/bin/env python3
"""
CLI script for chess analysis.
"""

import click
import chess.pgn
import json
import sys
import os
import io
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chess_analyzer.engine import ChessEngine
from chess_analyzer.evaluator import MoveEvaluator
from chess_analyzer.annotator import PGNAnnotator
from chess_analyzer.models import GameAnalysis, AnalysisResult


@click.command()
@click.option('--pgn', '-p', required=True, help='Input PGN file path')
@click.option('--engine', '-e', required=True, help='Path to Stockfish executable')
@click.option('--output', '-o', help='Output PGN file path (optional)')
@click.option('--shallow-depth', '-s', default=10, help='Shallow analysis depth (default: 10)')
@click.option('--deep-depth', '-d', default=20, help='Deep analysis depth (default: 20)')
@click.option('--multipv', '-m', default=3, help='Number of top moves to analyze (default: 3)')
@click.option('--json-output', '-j', help='Output JSON results to file (optional)')
@click.option('--summary-only', is_flag=True, help='Show only summary, not detailed analysis')
@click.option('--quiet', '-q', is_flag=True, help='Suppress progress output')
def analyze(
    pgn: str,
    engine: str,
    output: Optional[str],
    shallow_depth: int,
    deep_depth: int,
    multipv: int,
    json_output: Optional[str],
    summary_only: bool,
    quiet: bool
):
    """
    Analyze chess games from PGN file using Stockfish engine.
    
    This tool analyzes chess games and labels each move as Top, Excellent, Good, 
    Mistake, or Blunder based on centipawn loss. It also detects brilliant moves
    based on sacrifice, only-move, and surprise heuristics.
    """
    
    # Validate inputs
    if not os.path.exists(pgn):
        click.echo(f"Error: PGN file '{pgn}' not found.", err=True)
        sys.exit(1)
    
    if not os.path.exists(engine):
        click.echo(f"Error: Engine file '{engine}' not found.", err=True)
        sys.exit(1)
    
    # Read PGN file
    try:
        with open(pgn, 'r', encoding='utf-8') as f:
            pgn_content = f.read()
    except Exception as e:
        click.echo(f"Error reading PGN file: {e}", err=True)
        sys.exit(1)
    
    # Parse PGN
    try:
        pgn_io = io.StringIO(pgn_content)
        games = []
        
        while True:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            games.append(game)
        
        if not games:
            click.echo("Error: No valid games found in PGN file.", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error parsing PGN: {e}", err=True)
        sys.exit(1)
    
    click.echo(f"Found {len(games)} game(s) to analyze.")
    
    # Initialize engine and evaluator
    try:
        if not quiet:
            click.echo("Initializing chess engine...")
        
        chess_engine = ChessEngine(engine)
        evaluator = MoveEvaluator(chess_engine)
        
    except Exception as e:
        click.echo(f"Error initializing chess engine: {e}", err=True)
        sys.exit(1)
    
    try:
        # Analyze each game
        game_analyses = []
        
        for i, game in enumerate(games, 1):
            if not quiet:
                click.echo(f"Analyzing game {i}/{len(games)}...")
            
            # Evaluate the game
            move_assessments = evaluator.evaluate_game(
                game, 
                shallow_depth, 
                deep_depth, 
                multipv
            )
            
            # Create game analysis
            game_analysis = GameAnalysis(
                pgn=str(game),
                game=game,
                moves=move_assessments
            )
            
            game_analyses.append(game_analysis)
            
            # Create annotator and generate enhanced output
            annotator = PGNAnnotator()
            
            # Display enhanced analysis
            print("\n" + "=" * 80)
            print("CHESS ANALYSIS AI - ENHANCED PLAYER ACCURACY REPORT")
            print("=" * 80)
            
            # Game summary panel
            if game_analysis.white_stats and game_analysis.black_stats:
                print("\n" + annotator.create_simple_game_summary(game_analysis))
            
            # Player accuracy table
            if game_analysis.white_stats and game_analysis.black_stats:
                print("\n" + annotator.create_simple_player_accuracy_table(game_analysis))
            
            # Move-by-move analysis
            print("\n" + "=" * 80)
            print("MOVE-BY-MOVE ANALYSIS")
            print("=" * 80)
            print("")
            
            # Header
            print(f"{'Move':<6} {'Player':<6} {'Move':<8} {'Quality':<12} {'CP Loss':<10} {'Details'}")
            print("-" * 80)
            
            # Moves
            for move in game_analysis.moves:
                player = "W" if move.is_white else "B"
                quality = move.label
                cp_loss = f"-{move.loss_vs_best}" if move.loss_vs_best > 0 else "0"
                
                details = []
                if move.brilliant:
                    details.append("!! Brilliant")
                if move.is_only_move:
                    details.append("[Only move]")
                if move.is_sacrifice:
                    details.append("[Sacrifice]")
                if move.is_surprise:
                    details.append("[Surprise]")
                
                details_str = " ".join(details)
                
                print(f"{move.move_number:<6} {player:<6} {move.san:<8} {quality:<12} {cp_loss:<10} {details_str}")
            
            print("\n" + "=" * 80)
            print("ANALYSIS COMPLETE")
            print("=" * 80)
            
            # Save annotated PGN if requested
            if output:
                annotated_pgn = annotator.annotate_game(game_analysis)
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(annotated_pgn)
                click.echo(f"\n✅ Annotated PGN saved to: {output}")
            
            # Save JSON results if requested
            if json_output:
                with open(json_output, 'w', encoding='utf-8') as f:
                    json.dump(game_analysis.to_dict(), f, indent=2, ensure_ascii=False)
                click.echo(f"✅ JSON results saved to: {json_output}")
            
            # Display final summary
            if game_analysis.white_stats and game_analysis.black_stats:
                ws = game_analysis.white_stats
                bs = game_analysis.black_stats
                winner = ws.name if ws.accuracy_percentage > bs.accuracy_percentage else bs.name
                accuracy_diff = abs(ws.accuracy_percentage - bs.accuracy_percentage)
                
                print(f"\n🏆 GAME RESULT: {winner} wins with +{accuracy_diff:.1f}% accuracy advantage")
                print(f"📊 Overall Game Quality: {game_analysis.overall_quality} ({game_analysis.game_accuracy:.1f}% average accuracy)")
                print(f"♟️  Total Moves Analyzed: {game_analysis.total_moves}")
                print(f"✨ Total Brilliant Moves: {ws.brilliant_moves + bs.brilliant_moves}")
        
    finally:
        # Clean up
        chess_engine.close()


@click.command()
@click.option('--pgn', '-p', required=True, help='Input PGN file path')
@click.option('--engine', '-e', required=True, help='Path to Stockfish executable')
@click.option('--depth', default=15, help='Analysis depth (default: 15)')
@click.option('--multipv', default=5, help='Number of top moves to analyze (default: 5)')
def quick_analyze(pgn: str, engine: str, depth: int, multipv: int):
    """
    Quick analysis of a single game with basic move evaluation.
    """
    
    # Validate inputs
    if not os.path.exists(pgn):
        click.echo(f"Error: PGN file '{pgn}' not found.", err=True)
        sys.exit(1)
    
    if not os.path.exists(engine):
        click.echo(f"Error: Engine file '{engine}' not found.", err=True)
        sys.exit(1)
    
    # Read and parse PGN
    try:
        with open(pgn, 'r', encoding='utf-8') as f:
            pgn_content = f.read()
        
        pgn_io = io.StringIO(pgn_content)
        game = chess.pgn.read_game(pgn_io)
        
        if game is None:
            click.echo("Error: No valid game found in PGN file.", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error reading/parsing PGN: {e}", err=True)
        sys.exit(1)
    
    # Initialize engine
    try:
        click.echo("Initializing chess engine...")
        chess_engine = ChessEngine(engine)
        
    except Exception as e:
        click.echo(f"Error initializing chess engine: {e}", err=True)
        sys.exit(1)
    
    try:
        # Quick analysis
        click.echo(f"Analyzing game at depth {depth}...")
        
        board = game.board()
        move_number = 1
        
        click.echo("\nMove Analysis:")
        click.echo("-" * 50)
        
        for node in game.mainline():
            if node.move:
                # Get evaluation before move
                eval_before = chess_engine.get_evaluation(board, depth)
                
                # Get top moves
                top_moves = chess_engine.get_top_moves(board, depth, multipv)
                
                # Make the move
                board.push(node.move)
                eval_after = chess_engine.get_evaluation(board, depth)
                
                # Calculate centipawn change
                cp_change = eval_after - eval_before
                
                # Format output
                color = "W" if node.turn() else "B"
                move_san = board.san(node.move)
                
                click.echo(f"{move_number:2d}. {color} {move_san:6s} Δcp={cp_change:+4d}")
                
                # Show top alternatives
                if top_moves and len(top_moves) > 1:
                    best_move = top_moves[0][0]
                    if best_move != move_san:
                        click.echo(f"     Best: {best_move}")
                
                move_number += 1
        
        click.echo(f"\nAnalysis complete. Analyzed {move_number-1} moves.")
        
    finally:
        chess_engine.close()


@click.group()
def cli():
    """Chess Analysis AI - Top & Brilliant Move Detector"""
    pass


cli.add_command(analyze)
cli.add_command(quick_analyze)


if __name__ == '__main__':
    cli()
