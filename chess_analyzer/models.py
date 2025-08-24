"""
Data models for chess analysis results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import chess.pgn


class MoveLabel(str, Enum):
    """Move quality labels based on centipawn loss."""
    TOP = "Top"
    EXCELLENT = "Excellent"
    GOOD = "Good"
    MISTAKE = "Mistake"
    BLUNDER = "Blunder"


@dataclass
class PlayerStats:
    """Statistics for a single player (White or Black)."""
    name: str
    total_moves: int = 0
    top_moves: int = 0
    excellent_moves: int = 0
    good_moves: int = 0
    mistake_moves: int = 0
    blunder_moves: int = 0
    brilliant_moves: int = 0
    accuracy_percentage: float = 0.0
    blunder_rate: float = 0.0
    average_cp_loss: float = 0.0
    total_cp_loss: int = 0
    
    def __post_init__(self):
        """Calculate derived statistics."""
        if self.total_moves > 0:
            self.accuracy_percentage = round(
                (self.top_moves + self.excellent_moves + self.good_moves) / self.total_moves * 100, 1
            )
            self.blunder_rate = round(self.blunder_moves / self.total_moves * 100, 1)
            self.average_cp_loss = round(self.total_cp_loss / self.total_moves, 1)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "total_moves": self.total_moves,
            "top_moves": self.top_moves,
            "excellent_moves": self.excellent_moves,
            "good_moves": self.good_moves,
            "mistake_moves": self.mistake_moves,
            "blunder_moves": self.blunder_moves,
            "brilliant_moves": self.brilliant_moves,
            "accuracy_percentage": self.accuracy_percentage,
            "blunder_rate": self.blunder_rate,
            "average_cp_loss": self.average_cp_loss,
            "total_cp_loss": self.total_cp_loss
        }


@dataclass
class MoveAssessment:
    """Assessment of a single chess move."""
    move: str
    move_number: int
    is_white: bool
    san: str
    uci: str
    cp_gain: int
    loss_vs_best: int
    best_move: str
    label: MoveLabel
    brilliant: bool = False
    is_only_move: bool = False
    is_sacrifice: bool = False
    is_surprise: bool = False
    eval_before: int = 0
    eval_after: int = 0
    material_change: int = 0
    shallow_depth: int = 10
    deep_depth: int = 20
    multipv_count: int = 3
    
    def to_dict(self) -> Dict:
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
            "label": self.label,
            "brilliant": self.brilliant,
            "is_only_move": self.is_only_move,
            "is_sacrifice": self.is_sacrifice,
            "is_surprise": self.is_surprise,
            "eval_before": self.eval_before,
            "eval_after": self.eval_after,
            "material_change": self.material_change,
            "shallow_depth": self.shallow_depth,
            "deep_depth": self.deep_depth,
            "multipv_count": self.multipv_count
        }


@dataclass
class GameAnalysis:
    """Analysis results for a single chess game."""
    pgn: str
    game: any  # chess.pgn.Game object
    moves: List[MoveAssessment] = field(default_factory=list)
    total_moves: int = 0
    white_stats: Optional[PlayerStats] = None
    black_stats: Optional[PlayerStats] = None
    game_accuracy: float = 0.0
    overall_quality: str = ""
    
    def __post_init__(self):
        """Calculate game-level statistics."""
        if self.moves:
            self.total_moves = len(self.moves)
            self._calculate_player_stats()
            self._calculate_game_quality()
    
    def _calculate_player_stats(self):
        """Calculate statistics for each player."""
        white_moves = [m for m in self.moves if m.is_white]
        black_moves = [m for m in self.moves if not m.is_white]
        
        # Get player names from game
        white_name = getattr(self.game.headers.get('White', 'White'), 'value', 'White')
        black_name = getattr(self.game.headers.get('Black', 'Black'), 'value', 'Black')
        
        self.white_stats = self._create_player_stats(white_name, white_moves)
        self.black_stats = self._create_player_stats(black_name, black_moves)
    
    def _create_player_stats(self, name: str, moves: List[MoveAssessment]) -> PlayerStats:
        """Create player statistics from moves."""
        stats = PlayerStats(name=name, total_moves=len(moves))
        
        for move in moves:
            stats.total_cp_loss += abs(move.loss_vs_best)
            
            if move.label == MoveLabel.TOP:
                stats.top_moves += 1
            elif move.label == MoveLabel.EXCELLENT:
                stats.excellent_moves += 1
            elif move.label == MoveLabel.GOOD:
                stats.good_moves += 1
            elif move.label == MoveLabel.MISTAKE:
                stats.mistake_moves += 1
            elif move.label == MoveLabel.BLUNDER:
                stats.blunder_moves += 1
            
            if move.brilliant:
                stats.brilliant_moves += 1
        
        # Trigger post_init to calculate percentages
        stats.__post_init__()
        return stats
    
    def _calculate_game_quality(self):
        """Calculate overall game quality rating."""
        if not self.white_stats or not self.black_stats:
            return
        
        avg_accuracy = (self.white_stats.accuracy_percentage + self.black_stats.accuracy_percentage) / 2
        self.game_accuracy = round(avg_accuracy, 1)
        
        if avg_accuracy >= 80:
            self.overall_quality = "Excellent"
        elif avg_accuracy >= 60:
            self.overall_quality = "Good"
        elif avg_accuracy >= 40:
            self.overall_quality = "Fair"
        else:
            self.overall_quality = "Poor"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "pgn": self.pgn,
            "total_moves": self.total_moves,
            "white_stats": self.white_stats.to_dict() if self.white_stats else None,
            "black_stats": self.black_stats.to_dict() if self.black_stats else None,
            "game_accuracy": self.game_accuracy,
            "overall_quality": self.overall_quality,
            "moves": [move.to_dict() for move in self.moves]
        }


@dataclass
class AnalysisResult:
    """Results of analyzing multiple chess games."""
    games: List[GameAnalysis] = field(default_factory=list)
    total_games: int = 0
    total_moves: int = 0
    
    def __post_init__(self):
        """Calculate total statistics."""
        if self.games:
            self.total_games = len(self.games)
            self.total_moves = sum(game.total_moves for game in self.games)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "games": [game.to_dict() for game in self.games],
            "total_games": self.total_games,
            "total_moves": self.total_moves
        }
