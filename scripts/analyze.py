#!/usr/bin/env python3
"""
CLI script for chess analysis.
"""

import click
import chess.pgn
import json
import sys
import os
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
        annotator = PGNAnnotator()
        
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
                moves=move_assessments,
                total_moves=len(move_assessments)
            )
            
            game_analyses.append(game_analysis)
            
            if not quiet:
                click.echo(f"  Completed: {len(move_assessments)} moves analyzed")
        
        # Create batch result
        batch_result = AnalysisResult(
            games=game_analyses,
            total_games=len(game_analyses),
            total_moves=0  # Will be calculated in __post_init__
        )
        
        # Show summary
        if not quiet:
            click.echo("\n" + "="*60)
            click.echo("ANALYSIS COMPLETE")
            click.echo("="*60)
        
        summary = annotator.create_batch_summary(game_analyses)
        click.echo(summary)
        
        # Show detailed analysis if requested
        if not summary_only and not quiet:
            for i, game_analysis in enumerate(game_analyses, 1):
                click.echo(f"\nDetailed Analysis - Game {i}:")
                click.echo("-" * 40)
                detailed_summary = annotator.create_summary_table(game_analysis)
                click.echo(detailed_summary)
        
        # Save annotated PGN if output specified
        if output:
            try:
                annotated_pgns = annotator.batch_annotate_games(game_analyses)
                
                with open(output, 'w', encoding='utf-8') as f:
                    for annotated_pgn in annotated_pgns:
                        f.write(annotated_pgn + "\n\n")
                
                click.echo(f"\nAnnotated PGN saved to: {output}")
                
            except Exception as e:
                click.echo(f"Warning: Failed to save annotated PGN: {e}", err=True)
        
        # Save JSON results if requested
        if json_output:
            try:
                with open(json_output, 'w', encoding='utf-8') as f:
                    json.dump(batch_result.to_dict(), f, indent=2, ensure_ascii=False)
                
                click.echo(f"JSON results saved to: {json_output}")
                
            except Exception as e:
                click.echo(f"Warning: Failed to save JSON results: {e}", err=True)
        
        # Show final statistics
        if not quiet:
            click.echo(f"\nTotal games analyzed: {len(game_analyses)}")
            click.echo(f"Total moves analyzed: {batch_result.total_moves}")
            click.echo(f"Total brilliant moves found: {batch_result.overall_brilliant_count}")
            
            # Show move quality distribution
            click.echo("\nOverall Move Quality Distribution:")
            for label, count in batch_result.overall_move_distribution.items():
                percentage = (count / batch_result.total_moves) * 100 if batch_result.total_moves > 0 else 0
                click.echo(f"  {label.value}: {count} ({percentage:.1f}%)")
    
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
    # Add missing import
    import io
    cli()
