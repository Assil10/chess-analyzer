"""
Unit tests for chess analysis models.
"""

import pytest
from chess_analyzer.models import MoveLabel, MoveAssessment, GameAnalysis, AnalysisResult
import chess.pgn


class TestMoveLabel:
    """Test MoveLabel enum."""
    
    def test_move_label_values(self):
        """Test that MoveLabel has correct values."""
        assert MoveLabel.TOP == "Top"
        assert MoveLabel.EXCELLENT == "Excellent"
        assert MoveLabel.GOOD == "Good"
        assert MoveLabel.MISTAKE == "Mistake"
        assert MoveLabel.BLUNDER == "Blunder"


class TestMoveAssessment:
    """Test MoveAssessment dataclass."""
    
    def test_move_assessment_creation(self):
        """Test creating a MoveAssessment instance."""
        assessment = MoveAssessment(
            move="e4",
            move_number=1,
            is_white=True,
            san="e4",
            uci="e2e4",
            cp_gain=30,
            loss_vs_best=0,
            best_move="e4",
            label=MoveLabel.TOP,
            brilliant=True
        )
        
        assert assessment.move == "e4"
        assert assessment.move_number == 1
        assert assessment.is_white is True
        assert assessment.san == "e4"
        assert assessment.uci == "e2e4"
        assert assessment.cp_gain == 30
        assert assessment.loss_vs_best == 0
        assert assessment.best_move == "e4"
        assert assessment.label == MoveLabel.TOP
        assert assessment.brilliant is True
        assert assessment.is_only_move is False
        assert assessment.is_sacrifice is False
        assert assessment.is_surprise is False
    
    def test_move_assessment_defaults(self):
        """Test MoveAssessment with default values."""
        assessment = MoveAssessment(
            move="e4",
            move_number=1,
            is_white=True,
            san="e4",
            uci="e2e4",
            cp_gain=0,
            loss_vs_best=0,
            best_move="e4",
            label=MoveLabel.TOP
        )
        
        assert assessment.brilliant is False
        assert assessment.is_only_move is False
        assert assessment.is_sacrifice is False
        assert assessment.is_surprise is False
        assert assessment.eval_before == 0
        assert assessment.eval_after == 0
        assert assessment.material_change == 0
        assert assessment.shallow_depth == 10
        assert assessment.deep_depth == 20
        assert assessment.multipv_count == 3
    
    def test_move_assessment_to_dict(self):
        """Test MoveAssessment.to_dict() method."""
        assessment = MoveAssessment(
            move="e4",
            move_number=1,
            is_white=True,
            san="e4",
            uci="e2e4",
            cp_gain=30,
            loss_vs_best=0,
            best_move="e4",
            label=MoveLabel.TOP,
            brilliant=True
        )
        
        result = assessment.to_dict()
        
        assert isinstance(result, dict)
        assert result["move"] == "e4"
        assert result["label"] == "Top"
        assert result["brilliant"] is True
        assert result["cp_gain"] == 30


class TestGameAnalysis:
    """Test GameAnalysis dataclass."""
    
    def test_game_analysis_creation(self):
        """Test creating a GameAnalysis instance."""
        # Create a simple game
        game = chess.pgn.Game()
        game.add_variation(chess.Move.from_uci("e2e4"))
        
        moves = [
            MoveAssessment(
                move="e4",
                move_number=1,
                is_white=True,
                san="e4",
                uci="e2e4",
                cp_gain=30,
                loss_vs_best=0,
                best_move="e4",
                label=MoveLabel.TOP
            )
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4",
            game=game,
            moves=moves,
            total_moves=1
        )
        
        assert game_analysis.pgn == "1. e4"
        assert game_analysis.total_moves == 1
        assert len(game_analysis.moves) == 1
        assert game_analysis.white_score == 0.0
        assert game_analysis.black_score == 0.0
    
    def test_game_analysis_post_init(self):
        """Test GameAnalysis __post_init__ method."""
        game = chess.pgn.Game()
        game.add_variation(chess.Move.from_uci("e2e4"))
        
        moves = [
            MoveAssessment(
                move="e4",
                move_number=1,
                is_white=True,
                san="e4",
                uci="e2e4",
                cp_gain=30,
                loss_vs_best=0,
                best_move="e4",
                label=MoveLabel.TOP,
                brilliant=True
            ),
            MoveAssessment(
                move="e5",
                move_number=2,
                is_white=False,
                san="e5",
                uci="e7e5",
                cp_gain=-20,
                loss_vs_best=50,
                best_move="e5",
                label=MoveLabel.EXCELLENT
            )
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4 e5",
            game=game,
            moves=moves,
            total_moves=2
        )
        
        # Check move counts
        assert game_analysis.move_counts[MoveLabel.TOP] == 1
        assert game_analysis.move_counts[MoveLabel.EXCELLENT] == 1
        assert game_analysis.move_counts[MoveLabel.GOOD] == 0
        assert game_analysis.move_counts[MoveLabel.MISTAKE] == 0
        assert game_analysis.move_counts[MoveLabel.BLUNDER] == 0
        
        # Check brilliant count
        assert game_analysis.brilliant_count == 1
    
    def test_game_analysis_to_dict(self):
        """Test GameAnalysis.to_dict() method."""
        game = chess.pgn.Game()
        game.add_variation(chess.Move.from_uci("e2e4"))
        
        moves = [
            MoveAssessment(
                move="e4",
                move_number=1,
                is_white=True,
                san="e4",
                uci="e2e4",
                cp_gain=30,
                loss_vs_best=0,
                best_move="e4",
                label=MoveLabel.TOP
            )
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4",
            game=game,
            moves=moves,
            total_moves=1
        )
        
        result = game_analysis.to_dict()
        
        assert isinstance(result, dict)
        assert result["pgn"] == "1. e4"
        assert result["total_moves"] == 1
        assert result["brilliant_count"] == 0
        assert len(result["moves"]) == 1


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""
    
    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult instance."""
        # Create mock game analyses
        game1 = chess.pgn.Game()
        game1.add_variation(chess.Move.from_uci("e2e4"))
        
        game2 = chess.pgn.Game()
        game2.add_variation(chess.Move.from_uci("d2d4"))
        
        moves1 = [
            MoveAssessment(
                move="e4",
                move_number=1,
                is_white=True,
                san="e4",
                uci="e2e4",
                cp_gain=30,
                loss_vs_best=0,
                best_move="e4",
                label=MoveLabel.TOP
            )
        ]
        
        moves2 = [
            MoveAssessment(
                move="d4",
                move_number=1,
                is_white=True,
                san="d4",
                uci="d2d4",
                cp_gain=25,
                loss_vs_best=5,
                best_move="d4",
                label=MoveLabel.TOP
            )
        ]
        
        game_analysis1 = GameAnalysis(
            pgn="1. e4",
            game=game1,
            moves=moves1,
            total_moves=1
        )
        
        game_analysis2 = GameAnalysis(
            pgn="1. d4",
            game=game2,
            moves=moves2,
            total_moves=1
        )
        
        analysis_result = AnalysisResult(
            games=[game_analysis1, game_analysis2],
            total_games=2,
            total_moves=0
        )
        
        assert analysis_result.total_games == 2
        assert analysis_result.total_moves == 2  # Calculated in __post_init__
        assert analysis_result.overall_brilliant_count == 0
        assert len(analysis_result.overall_move_distribution) == 5  # All MoveLabel values
    
    def test_analysis_result_to_dict(self):
        """Test AnalysisResult.to_dict() method."""
        game = chess.pgn.Game()
        game.add_variation(chess.Move.from_uci("e2e4"))
        
        moves = [
            MoveAssessment(
                move="e4",
                move_number=1,
                is_white=True,
                san="e4",
                uci="e2e4",
                cp_gain=30,
                loss_vs_best=0,
                best_move="e4",
                label=MoveLabel.TOP
            )
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4",
            game=game,
            moves=moves,
            total_moves=1
        )
        
        analysis_result = AnalysisResult(
            games=[game_analysis],
            total_games=1,
            total_moves=0
        )
        
        result = analysis_result.to_dict()
        
        assert isinstance(result, dict)
        assert result["total_games"] == 1
        assert result["total_moves"] == 1
        assert result["overall_brilliant_count"] == 0
        assert len(result["games"]) == 1


if __name__ == "__main__":
    pytest.main([__file__])
