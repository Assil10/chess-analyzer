"""
PGN annotation with analysis results and comments.
"""

import chess
import chess.pgn
from typing import List, Dict, Any, Optional
from .models import MoveAssessment, GameAnalysis
import logging

logger = logging.getLogger(__name__)


class PGNAnnotator:
    """Annotates PGN files with analysis results and comments."""
    
    def __init__(self):
        """Initialize the PGN annotator."""
        # NAG (Numeric Annotation Glyph) mappings
        self.nag_mapping = {
            "Top": "!",           # Good move
            "Excellent": "!!",    # Excellent move
            "Good": "!?",         # Interesting move
            "Mistake": "?",       # Mistake
            "Blunder": "??"       # Blunder
        }
        
        # Comment templates
        self.comment_templates = {
            "brilliant": "!! Brilliant",
            "only_move": "[Only move]",
            "sacrifice": "[Sacrifice]",
            "surprise": "[Surprise]",
            "cp_gain": "Δcp={:+d}",
            "best_move": "Best: {}",
            "loss_vs_best": "Loss: {}cp"
        }
    
    def annotate_game(self, game_analysis: GameAnalysis) -> str:
        """
        Annotate a chess game with analysis results.
        
        Args:
            game_analysis: GameAnalysis object with move assessments
            
        Returns:
            Annotated PGN string
        """
        # Create a copy of the game for annotation
        game = game_analysis.game.copy()
        
        # Annotate each move
        self._annotate_moves(game, game_analysis.moves)
        
        # Export to PGN string
        return str(game)
    
    def _annotate_moves(self, game: chess.pgn.Game, assessments: List[MoveAssessment]) -> None:
        """Annotate moves in the game with analysis results."""
        # Create a mapping of move number to assessment
        assessment_map = {}
        for assessment in assessments:
            assessment_map[assessment.move_number] = assessment
        
        # Traverse the game and annotate moves
        board = game.board()
        move_number = 1
        
        for node in game.mainline():
            if node.move and move_number in assessment_map:
                assessment = assessment_map[move_number]
                
                # Add NAG (Numeric Annotation Glyph)
                nag = self._get_nag(assessment.label)
                if nag:
                    node.nags.add(nag)
                
                # Add comments
                comments = self._generate_comments(assessment)
                if comments:
                    node.comment = " ".join(comments)
                
                # Make the move
                board.push(node.move)
                move_number += 1
    
    def _get_nag(self, label: str) -> Optional[int]:
        """Get NAG value for a move label."""
        nag_string = self.nag_mapping.get(label)
        if nag_string == "!":
            return chess.pgn.NAG_GOOD_MOVE
        elif nag_string == "!!":
            return chess.pgn.NAG_BRILLIANT_MOVE
        elif nag_string == "!?":
            return chess.pgn.NAG_SPECULATIVE_MOVE
        elif nag_string == "?":
            return chess.pgn.NAG_MISTAKE
        elif nag_string == "??":
            return chess.pgn.NAG_BLUNDER
        return None
    
    def _generate_comments(self, assessment: MoveAssessment) -> List[str]:
        """Generate comments for a move assessment."""
        comments = []
        
        # Add brilliant comment
        if assessment.brilliant:
            comments.append(self.comment_templates["brilliant"])
        
        # Add heuristic comments
        if assessment.is_only_move:
            comments.append(self.comment_templates["only_move"])
        
        if assessment.is_sacrifice:
            comments.append(self.comment_templates["sacrifice"])
        
        if assessment.is_surprise:
            comments.append(self.comment_templates["surprise"])
        
        # Add centipawn gain/loss
        if assessment.cp_gain != 0:
            cp_comment = self.comment_templates["cp_gain"].format(assessment.cp_gain)
            comments.append(cp_comment)
        
        # Add loss vs best move
        if assessment.loss_vs_best > 0:
            loss_comment = self.comment_templates["loss_vs_best"].format(assessment.loss_vs_best)
            comments.append(loss_comment)
        
        # Add best move if different from played move
        if assessment.best_move != assessment.move:
            best_comment = self.comment_templates["best_move"].format(assessment.best_move)
            comments.append(best_comment)
        
        return comments
    
    def create_summary_table(self, game_analysis: GameAnalysis) -> str:
        """
        Create a summary table of the game analysis.
        
        Args:
            game_analysis: GameAnalysis object
            
        Returns:
            Formatted summary table string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"Game Analysis Summary")
        lines.append("=" * 80)
        
        # Game statistics
        lines.append(f"Total Moves: {game_analysis.total_moves}")
        lines.append(f"Brilliant Moves: {game_analysis.brilliant_count}")
        lines.append("")
        
        # Move distribution
        lines.append("Move Quality Distribution:")
        for label, count in game_analysis.move_counts.items():
            percentage = (count / game_analysis.total_moves) * 100
            lines.append(f"  {label.value}: {count} ({percentage:.1f}%)")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("Move-by-Move Analysis:")
        lines.append("=" * 80)
        
        # Move details
        for assessment in game_analysis.moves:
            color = "W" if assessment.is_white else "B"
            move_num = assessment.move_number
            
            # Format the move line
            move_line = f"{move_num:2d}. {color} {assessment.move:6s}"
            
            # Add label
            label_str = f"[{assessment.label.value}]"
            move_line += f" {label_str:12s}"
            
            # Add centipawn info
            cp_str = f"Δcp={assessment.cp_gain:+4d}"
            move_line += f" {cp_str:10s}"
            
            # Add loss vs best
            if assessment.loss_vs_best > 0:
                loss_str = f"(-{assessment.loss_vs_best:3d}cp)"
                move_line += f" {loss_str:10s}"
            else:
                move_line += " " * 10
            
            # Add brilliant indicator
            if assessment.brilliant:
                move_line += " !!"
            
            # Add heuristics
            heuristics = []
            if assessment.is_only_move:
                heuristics.append("OM")
            if assessment.is_sacrifice:
                heuristics.append("SAC")
            if assessment.is_surprise:
                heuristics.append("SUR")
            
            if heuristics:
                move_line += f" [{', '.join(heuristics)}]"
            
            lines.append(move_line)
        
        return "\n".join(lines)
    
    def export_json_summary(self, game_analysis: GameAnalysis) -> Dict[str, Any]:
        """
        Export game analysis as JSON-compatible dictionary.
        
        Args:
            game_analysis: GameAnalysis object
            
        Returns:
            Dictionary representation of the analysis
        """
        return game_analysis.to_dict()
    
    def batch_annotate_games(self, game_analyses: List[GameAnalysis]) -> List[str]:
        """
        Annotate multiple games.
        
        Args:
            game_analyses: List of GameAnalysis objects
            
        Returns:
            List of annotated PGN strings
        """
        annotated_pgns = []
        
        for game_analysis in game_analyses:
            try:
                annotated_pgn = self.annotate_game(game_analysis)
                annotated_pgns.append(annotated_pgn)
            except Exception as e:
                logger.error(f"Failed to annotate game: {e}")
                # Return original PGN if annotation fails
                annotated_pgns.append(game_analysis.pgn)
        
        return annotated_pgns
    
    def create_batch_summary(self, game_analyses: List[GameAnalysis]) -> str:
        """
        Create a summary of multiple game analyses.
        
        Args:
            game_analyses: List of GameAnalysis objects
            
        Returns:
            Formatted batch summary string
        """
        if not game_analyses:
            return "No games to analyze."
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"Batch Analysis Summary - {len(game_analyses)} Games")
        lines.append("=" * 80)
        
        # Overall statistics
        total_moves = sum(game.total_moves for game in game_analyses)
        total_brilliant = sum(game.brilliant_count for game in game_analyses)
        
        lines.append(f"Total Games: {len(game_analyses)}")
        lines.append(f"Total Moves: {total_moves}")
        lines.append(f"Total Brilliant Moves: {total_brilliant}")
        lines.append("")
        
        # Per-game summary
        for i, game_analysis in enumerate(game_analyses, 1):
            lines.append(f"Game {i}:")
            lines.append(f"  Moves: {game_analysis.total_moves}")
            lines.append(f"  Brilliant: {game_analysis.brilliant_count}")
            
            # Top quality moves
            top_moves = game_analysis.move_counts.get("Top", 0)
            excellent_moves = game_analysis.move_counts.get("Excellent", 0)
            lines.append(f"  Top/Excellent: {top_moves}/{excellent_moves}")
            lines.append("")
        
        return "\n".join(lines)
