"""
PGN annotation and output formatting for chess analysis results.
"""

import chess.pgn
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

from .models import GameAnalysis, AnalysisResult, MoveLabel, PlayerStats


class PGNAnnotator:
    """Annotates PGN files with analysis results and generates formatted output."""
    
    def __init__(self):
        self.console = Console()
    
    def annotate_game(self, game_analysis: GameAnalysis) -> str:
        """Annotate a single game with analysis results."""
        if not game_analysis.moves:
            return str(game_analysis.game)
        
        # Create annotated PGN
        game = game_analysis.game
        board = game.board()
        
        # Add analysis comments to moves
        for move_assessment in game_analysis.moves:
            if move_assessment.move_number <= len(list(game.mainline_moves())):
                # Find the move in the game tree
                node = game
                for _ in range(move_assessment.move_number - 1):
                    if node.variations:
                        node = node.variations[0]
                    else:
                        break
                
                if node.variations:
                    # Add comment to the move
                    comment_parts = []
                    
                    # Quality label
                    comment_parts.append(f"[{move_assessment.label}]")
                    
                    # Centipawn loss
                    if move_assessment.loss_vs_best > 0:
                        comment_parts.append(f"Δcp=-{move_assessment.loss_vs_best}")
                    
                    # Brilliant move indicator
                    if move_assessment.brilliant:
                        comment_parts.append("!! Brilliant")
                    
                    # Special characteristics
                    if move_assessment.is_only_move:
                        comment_parts.append("[Only move]")
                    if move_assessment.is_sacrifice:
                        comment_parts.append("[Sacrifice]")
                    if move_assessment.is_surprise:
                        comment_parts.append("[Surprise]")
                    
                    # Combine comments
                    if comment_parts:
                        node.variations[0].comment = " ".join(comment_parts)
        
        return str(game)
    
    def create_player_accuracy_table(self, game_analysis: GameAnalysis) -> Table:
        """Create a detailed player accuracy table in Chess.com style."""
        table = Table(title="Player Accuracy Analysis", show_header=True, header_style="bold magenta")
        
        # Add columns
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("White", style="white", justify="center")
        table.add_column("Black", style="white", justify="center")
        table.add_column("Difference", style="yellow", justify="center")
        
        if not game_analysis.white_stats or not game_analysis.black_stats:
            return table
        
        ws = game_analysis.white_stats
        bs = game_analysis.black_stats
        
        # Player names
        table.add_row("Player", ws.name, bs.name, "")
        
        # Total moves
        table.add_row("Total Moves", str(ws.total_moves), str(bs.total_moves), "")
        
        # Move quality breakdown
        table.add_row("", "", "", "")
        table.add_row("Move Quality Breakdown:", "", "", "")
        
        # Top moves
        diff = ws.top_moves - bs.top_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        table.add_row("  Top", f"{ws.top_moves} ({ws.top_moves/ws.total_moves*100:.1f}%)", 
                     f"{bs.top_moves} ({bs.top_moves/bs.total_moves*100:.1f}%)", diff_str)
        
        # Excellent moves
        diff = ws.excellent_moves - bs.excellent_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        table.add_row("  Excellent", f"{ws.excellent_moves} ({ws.excellent_moves/ws.total_moves*100:.1f}%)", 
                     f"{bs.excellent_moves} ({bs.excellent_moves/bs.total_moves*100:.1f}%)", diff_str)
        
        # Good moves
        diff = ws.good_moves - bs.good_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        table.add_row("  Good", f"{ws.good_moves} ({ws.good_moves/ws.total_moves*100:.1f}%)", 
                     f"{bs.good_moves} ({bs.good_moves/bs.total_moves*100:.1f}%)", diff_str)
        
        # Mistakes
        diff = ws.mistake_moves - bs.mistake_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        table.add_row("  Mistake", f"{ws.mistake_moves} ({ws.mistake_moves/ws.total_moves*100:.1f}%)", 
                     f"{bs.mistake_moves} ({bs.mistake_moves/bs.total_moves*100:.1f}%)", diff_str)
        
        # Blunders
        diff = ws.blunder_moves - bs.blunder_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        table.add_row("  Blunder", f"{ws.blunder_moves} ({ws.blunder_moves/ws.total_moves*100:.1f}%)", 
                     f"{bs.blunder_moves} ({bs.blunder_moves/bs.total_moves*100:.1f}%)", diff_str)
        
        # Brilliant moves
        diff = ws.brilliant_moves - bs.brilliant_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        table.add_row("  Brilliant", str(ws.brilliant_moves), str(bs.brilliant_moves), diff_str)
        
        # Summary statistics
        table.add_row("", "", "", "")
        table.add_row("Summary Statistics:", "", "", "")
        
        # Accuracy
        diff = ws.accuracy_percentage - bs.accuracy_percentage
        diff_str = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%" if diff < 0 else "0.0%"
        table.add_row("  Accuracy", f"{ws.accuracy_percentage:.1f}%", f"{bs.accuracy_percentage:.1f}%", diff_str)
        
        # Blunder rate
        diff = bs.blunder_rate - ws.blunder_rate  # Lower is better
        diff_str = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%" if diff < 0 else "0.0%"
        table.add_row("  Blunder Rate", f"{ws.blunder_rate:.1f}%", f"{bs.blunder_rate:.1f}%", diff_str)
        
        # Average CP loss
        diff = bs.average_cp_loss - ws.average_cp_loss  # Lower is better
        diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}" if diff < 0 else "0.0"
        table.add_row("  Avg CP Loss", f"{ws.average_cp_loss:.1f}", f"{bs.average_cp_loss:.1f}", diff_str)
        
        return table
    
    def create_game_summary_panel(self, game_analysis: GameAnalysis) -> Panel:
        """Create a game summary panel with key statistics."""
        if not game_analysis.white_stats or not game_analysis.black_stats:
            return Panel("No game analysis available", title="Game Summary")
        
        ws = game_analysis.white_stats
        bs = game_analysis.black_stats
        
        # Determine winner based on accuracy
        winner = ws.name if ws.accuracy_percentage > bs.accuracy_percentage else bs.name
        accuracy_diff = abs(ws.accuracy_percentage - bs.accuracy_percentage)
        
        content = f"""
Game Quality: {game_analysis.overall_quality} ({game_analysis.game_accuracy:.1f}% average accuracy)

Winner: {winner} (+{accuracy_diff:.1f}% accuracy advantage)

{ws.name} (White): {ws.accuracy_percentage:.1f}% accuracy, {ws.blunder_rate:.1f}% blunder rate
{bs.name} (Black): {bs.accuracy_percentage:.1f}% accuracy, {bs.blunder_rate:.1f}% blunder rate

Total Moves: {game_analysis.total_moves}
Brilliant Moves: {ws.brilliant_moves + bs.brilliant_moves}
        """
        
        return Panel(content.strip(), title="Game Summary", border_style="green")
    
    def create_cli_summary(self, game_analysis: GameAnalysis) -> str:
        """Create a comprehensive CLI summary with player accuracy analysis."""
        if not game_analysis.moves:
            return "No moves to analyze."
        
        output = []
        output.append("=" * 80)
        output.append("CHESS ANALYSIS AI - PLAYER ACCURACY REPORT")
        output.append("=" * 80)
        output.append("")
        
        # Game summary panel
        if game_analysis.white_stats and game_analysis.black_stats:
            output.append(self.create_game_summary_panel(game_analysis).render())
            output.append("")
        
        # Player accuracy table
        if game_analysis.white_stats and game_analysis.black_stats:
            output.append(self.create_player_accuracy_table(game_analysis).render())
            output.append("")
        
        # Move-by-move analysis
        output.append("=" * 80)
        output.append("MOVE-BY-MOVE ANALYSIS")
        output.append("=" * 80)
        output.append("")
        
        # Header
        output.append(f"{'Move':<6} {'Player':<6} {'Move':<8} {'Quality':<12} {'CP Loss':<10} {'Details'}")
        output.append("-" * 80)
        
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
            
            output.append(f"{move.move_number:<6} {player:<6} {move.san:<8} {quality:<12} {cp_loss:<10} {details_str}")
        
        output.append("")
        output.append("=" * 80)
        output.append("ANALYSIS COMPLETE")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    def create_simple_game_summary(self, game_analysis: GameAnalysis) -> str:
        """Create a simple text-based game summary."""
        if not game_analysis.white_stats or not game_analysis.black_stats:
            return "No game analysis available"
        
        ws = game_analysis.white_stats
        bs = game_analysis.black_stats
        
        # Determine winner based on accuracy
        winner = ws.name if ws.accuracy_percentage > bs.accuracy_percentage else bs.name
        accuracy_diff = abs(ws.accuracy_percentage - bs.accuracy_percentage)
        
        content = f"""
Game Quality: {game_analysis.overall_quality} ({game_analysis.game_accuracy:.1f}% average accuracy)

Winner: {winner} (+{accuracy_diff:.1f}% accuracy advantage)

{ws.name} (White): {ws.accuracy_percentage:.1f}% accuracy, {ws.blunder_rate:.1f}% blunder rate
{bs.name} (Black): {bs.accuracy_percentage:.1f}% accuracy, {bs.blunder_rate:.1f}% blunder rate

Total Moves: {game_analysis.total_moves}
Brilliant Moves: {ws.brilliant_moves + bs.brilliant_moves}
        """
        
        return content.strip()
    
    def create_simple_player_accuracy_table(self, game_analysis: GameAnalysis) -> str:
        """Create a simple text-based player accuracy table."""
        if not game_analysis.white_stats or not game_analysis.black_stats:
            return "No player statistics available"
        
        ws = game_analysis.white_stats
        bs = game_analysis.black_stats
        
        output = []
        output.append("PLAYER ACCURACY ANALYSIS")
        output.append("=" * 60)
        output.append("")
        
        # Player names
        output.append(f"{'Metric':<20} {'White':<20} {'Black':<20}")
        output.append("-" * 60)
        
        # Total moves
        output.append(f"{'Total Moves':<20} {ws.total_moves:<20} {bs.total_moves:<20}")
        
        # Move quality breakdown
        output.append("")
        output.append("Move Quality Breakdown:")
        
        # Top moves
        diff = ws.top_moves - bs.top_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        output.append(f"{'  Top':<20} {ws.top_moves} ({ws.top_moves/ws.total_moves*100:.1f}%){'':<10} {bs.top_moves} ({bs.top_moves/bs.total_moves*100:.1f}%){'':<10} {diff_str}")
        
        # Excellent moves
        diff = ws.excellent_moves - bs.excellent_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        output.append(f"{'  Excellent':<20} {ws.excellent_moves} ({ws.excellent_moves/ws.total_moves*100:.1f}%){'':<10} {bs.excellent_moves} ({bs.excellent_moves/bs.total_moves*100:.1f}%){'':<10} {diff_str}")
        
        # Good moves
        diff = ws.good_moves - bs.good_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        output.append(f"{'  Good':<20} {ws.good_moves} ({ws.good_moves/ws.total_moves*100:.1f}%){'':<10} {bs.good_moves} ({bs.good_moves/bs.total_moves*100:.1f}%){'':<10} {diff_str}")
        
        # Mistakes
        diff = ws.mistake_moves - bs.mistake_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        output.append(f"{'  Mistake':<20} {ws.mistake_moves} ({ws.mistake_moves/ws.total_moves*100:.1f}%){'':<10} {bs.mistake_moves} ({bs.mistake_moves/bs.total_moves*100:.1f}%){'':<10} {diff_str}")
        
        # Blunders
        diff = ws.blunder_moves - bs.blunder_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        output.append(f"{'  Blunder':<20} {ws.blunder_moves} ({ws.blunder_moves/ws.total_moves*100:.1f}%){'':<10} {bs.blunder_moves} ({bs.blunder_moves/bs.total_moves*100:.1f}%){'':<10} {diff_str}")
        
        # Brilliant moves
        diff = ws.brilliant_moves - bs.brilliant_moves
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "0"
        output.append(f"{'  Brilliant':<20} {ws.brilliant_moves:<20} {bs.brilliant_moves:<20} {diff_str}")
        
        # Summary statistics
        output.append("")
        output.append("Summary Statistics:")
        
        # Accuracy
        diff = ws.accuracy_percentage - bs.accuracy_percentage
        diff_str = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%" if diff < 0 else "0.0%"
        output.append(f"{'  Accuracy':<20} {ws.accuracy_percentage:.1f}%{'':<15} {bs.accuracy_percentage:.1f}%{'':<15} {diff_str}")
        
        # Blunder rate
        diff = bs.blunder_rate - ws.blunder_rate  # Lower is better
        diff_str = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%" if diff < 0 else "0.0%"
        output.append(f"{'  Blunder Rate':<20} {ws.blunder_rate:.1f}%{'':<15} {bs.blunder_rate:.1f}%{'':<15} {diff_str}")
        
        # Average CP loss
        diff = bs.average_cp_loss - ws.average_cp_loss  # Lower is better
        diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}" if diff < 0 else "0.0"
        output.append(f"{'  Avg CP Loss':<20} {ws.average_cp_loss:.1f}{'':<15} {bs.average_cp_loss:.1f}{'':<15} {diff_str}")
        
        return "\n".join(output)
    
    def batch_annotate_games(self, game_analyses: List[GameAnalysis]) -> List[str]:
        """Annotate multiple games and return annotated PGNs."""
        return [self.annotate_game(game) for game in game_analyses]
    
    def create_batch_summary(self, game_analyses: List[GameAnalysis]) -> str:
        """Create a summary of batch analysis results."""
        if not game_analyses:
            return "No games analyzed."
        
        output = []
        output.append("=" * 80)
        output.append("BATCH ANALYSIS SUMMARY")
        output.append("=" * 80)
        output.append("")
        
        total_games = len(game_analyses)
        total_moves = sum(game.total_moves for game in game_analyses)
        total_brilliant = sum(
            (game.white_stats.brilliant_moves if game.white_stats else 0) + 
            (game.black_stats.brilliant_moves if game.black_stats else 0) 
            for game in game_analyses
        )
        
        output.append(f"Total Games Analyzed: {total_games}")
        output.append(f"Total Moves Analyzed: {total_moves}")
        output.append(f"Total Brilliant Moves: {total_brilliant}")
        output.append("")
        
        # Game-by-game summary
        for i, game in enumerate(game_analyses, 1):
            if game.white_stats and game.black_stats:
                winner = game.white_stats.name if game.white_stats.accuracy_percentage > game.black_stats.accuracy_percentage else game.black_stats.name
                accuracy_diff = abs(game.white_stats.accuracy_percentage - game.black_stats.accuracy_percentage)
                
                output.append(f"Game {i}: {game.white_stats.name} vs {game.black_stats.black_stats.name}")
                output.append(f"  Winner: {winner} (+{accuracy_diff:.1f}% accuracy)")
                output.append(f"  Quality: {game.overall_quality} ({game.game_accuracy:.1f}% avg)")
                output.append(f"  Moves: {game.total_moves}")
                output.append("")
        
        return "\n".join(output)
