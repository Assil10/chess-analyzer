"""
Data models for chess analysis results.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import chess.pgn


class MoveLabel(str, Enum):
    """Enumeration of move quality labels."""
    TOP = "Top"
    EXCELLENT = "Excellent"
    GOOD = "Good"
    MISTAKE = "Mistake"
    BLUNDER = "Blunder"


@dataclass
class MoveAssessment:
    """Assessment of a single chess move."""
    
    # Basic move information
    move: str
    move_number: int
    is_white: bool
    san: str
    uci: str
    
    # Evaluation data
    cp_gain: int  # Centipawn gain/loss
    loss_vs_best: int  # Centipawn loss compared to best move
    best_move: str  # Best move in SAN notation
    
    # Quality assessment
    label: MoveLabel
    brilliant: bool = False
    
    # Heuristics
    is_only_move: bool = False
    is_sacrifice: bool = False
    is_surprise: bool = False
    
    # Additional data
    eval_before: int = 0  # Evaluation before move
    eval_after: int = 0   # Evaluation after move
    material_change: int = 0  # Material change in pawn units
    
    # Engine analysis details
    shallow_depth: int = 10
    deep_depth: int = 20
    multipv_count: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "move": self.move,
            "move_number": self.move_number,
            "is_white": self.is_white,
            "san": self.san,
            "uci": self.uci,
            "cp_gain": self.cp_gain,
            "loss_vs_best": self.loss_vs_best,
            "best_move": self.best_move,
            "label": self.label.value,
            "brilliant": self.brilliant,
            "is_only_move": self.is_only_move,
            "is_sacrifice": self.is_sacrifice,
            "is_surprise": self.is_surprise,
            "eval_before": self.eval_before,
            "eval_after": self.eval_after,
            "material_change": self.material_change,
            "shallow_depth": self.shallow_depth,
            "deep_depth": self.deep_depth,
            "multipv_count": self.multipv_count,
        }


@dataclass
class GameAnalysis:
    """Complete analysis of a chess game."""
    
    # Game metadata
    pgn: str
    game: chess.pgn.Game
    
    # Analysis results
    moves: List[MoveAssessment]
    
    # Game statistics
    total_moves: int
    white_score: float = 0.0
    black_score: float = 0.0
    
    # Quality distribution
    move_counts: Dict[MoveLabel, int] = None
    brilliant_count: int = 0
    
    def __post_init__(self):
        """Initialize derived fields."""
        if self.move_counts is None:
            self.move_counts = {label: 0 for label in MoveLabel}
        
        # Count moves by label
        for move in self.moves:
            self.move_counts[move.label] += 1
            if move.brilliant:
                self.brilliant_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pgn": self.pgn,
            "total_moves": self.total_moves,
            "white_score": self.white_score,
            "black_score": self.black_score,
            "move_counts": {label.value: count for label, count in self.move_counts.items()},
            "brilliant_count": self.brilliant_count,
            "moves": [move.to_dict() for move in self.moves]
        }


@dataclass
class AnalysisResult:
    """Result of analyzing multiple games."""
    
    games: List[GameAnalysis]
    total_games: int
    total_moves: int
    
    # Overall statistics
    overall_brilliant_count: int = 0
    overall_move_distribution: Dict[MoveLabel, int] = None
    
    def __post_init__(self):
        """Initialize derived fields."""
        if self.overall_move_distribution is None:
            self.overall_move_distribution = {label: 0 for label in MoveLabel}
        
        # Aggregate statistics across all games
        for game in self.games:
            self.total_moves += game.total_moves
            self.overall_brilliant_count += game.brilliant_count
            
            for label, count in game.move_counts.items():
                self.overall_move_distribution[label] += count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_games": self.total_games,
            "total_moves": self.total_moves,
            "overall_brilliant_count": self.overall_brilliant_count,
            "overall_move_distribution": {label.value: count for label, count in self.overall_move_distribution.items()},
            "games": [game.to_dict() for game in self.games]
        }
