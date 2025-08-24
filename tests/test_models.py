"""
Unit tests for chess analysis data models.
"""

import pytest
import chess.pgn
from io import StringIO

from chess_analyzer.models import MoveLabel, MoveAssessment, GameAnalysis, AnalysisResult, PlayerStats


class TestMoveLabel:
    """Test MoveLabel enum."""
    
    def test_move_label_values(self):
        """Test that MoveLabel has the expected values."""
        assert MoveLabel.TOP == "Top"
        assert MoveLabel.EXCELLENT == "Excellent"
        assert MoveLabel.GOOD == "Good"
        assert MoveLabel.MISTAKE == "Mistake"
        assert MoveLabel.BLUNDER == "Blunder"


class TestPlayerStats:
    """Test PlayerStats class."""
    
    def test_player_stats_creation(self):
        """Test PlayerStats creation with basic data."""
        stats = PlayerStats(name="Test Player")
        assert stats.name == "Test Player"
        assert stats.total_moves == 0
        assert stats.accuracy_percentage == 0.0
        assert stats.blunder_rate == 0.0
    
    def test_player_stats_calculations(self):
        """Test that PlayerStats calculates percentages correctly."""
        stats = PlayerStats(
            name="Test Player",
            total_moves=10,
            top_moves=5,
            excellent_moves=2,
            good_moves=1,
            mistake_moves=1,
            blunder_moves=1,
            total_cp_loss=100
        )
        
        # Trigger post_init calculations
        stats.__post_init__()
        
        assert stats.accuracy_percentage == 80.0  # (5+2+1)/10 * 100
        assert stats.blunder_rate == 10.0  # 1/10 * 100
        assert stats.average_cp_loss == 10.0  # 100/10
    
    def test_player_stats_to_dict(self):
        """Test PlayerStats serialization."""
        stats = PlayerStats(name="Test Player", total_moves=5, top_moves=3)
        stats.__post_init__()
        
        result = stats.to_dict()
        assert result["name"] == "Test Player"
        assert result["total_moves"] == 5
        assert result["top_moves"] == 3
        assert result["accuracy_percentage"] == 60.0


class TestMoveAssessment:
    """Test MoveAssessment class."""
    
    def test_move_assessment_creation(self):
        """Test MoveAssessment creation with required fields."""
        assessment = MoveAssessment(
            move="e4",
            move_number=1,
            is_white=True,
            san="e4",
            uci="e2e4",
            cp_gain=50,
            loss_vs_best=0,
            best_move="e4",
            label=MoveLabel.TOP
        )
        
        assert assessment.move == "e4"
        assert assessment.move_number == 1
        assert assessment.is_white is True
        assert assessment.san == "e4"
        assert assessment.uci == "e2e4"
        assert assessment.cp_gain == 50
        assert assessment.loss_vs_best == 0
        assert assessment.best_move == "e4"
        assert assessment.label == MoveLabel.TOP
    
    def test_move_assessment_defaults(self):
        """Test MoveAssessment default values."""
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
        """Test MoveAssessment serialization."""
        assessment = MoveAssessment(
            move="e4",
            move_number=1,
            is_white=True,
            san="e4",
            uci="e2e4",
            cp_gain=50,
            loss_vs_best=0,
            best_move="e4",
            label=MoveLabel.TOP
        )
        
        result = assessment.to_dict()
        assert result["move"] == "e4"
        assert result["move_number"] == 1
        assert result["is_white"] is True
        assert result["san"] == "e4"
        assert result["uci"] == "e2e4"
        assert result["cp_gain"] == 50
        assert result["loss_vs_best"] == 0
        assert result["best_move"] == "e4"
        assert result["label"] == MoveLabel.TOP


class TestGameAnalysis:
    """Test GameAnalysis class."""
    
    def test_game_analysis_creation(self):
        """Test GameAnalysis creation."""
        # Create a simple game
        pgn = StringIO("1. e4 e5")
        game = chess.pgn.read_game(pgn)
        
        # Create move assessments
        moves = [
            MoveAssessment(
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
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4 e5",
            game=game,
            moves=moves
        )
        
        assert game_analysis.pgn == "1. e4 e5"
        assert game_analysis.game == game
        assert len(game_analysis.moves) == 1
        assert game_analysis.total_moves == 1
    
    def test_game_analysis_post_init(self):
        """Test that GameAnalysis calculates statistics correctly."""
        # Create a simple game
        pgn = StringIO("1. e4 e5")
        game = chess.pgn.read_game(pgn)
        
        # Create move assessments
        moves = [
            MoveAssessment(
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
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4 e5",
            game=game,
            moves=moves
        )
        
        # Check that player stats were calculated
        assert game_analysis.white_stats is not None
        assert game_analysis.black_stats is not None
        assert game_analysis.white_stats.total_moves == 1
        assert game_analysis.black_stats.total_moves == 0  # No black moves in this simple game
        assert game_analysis.white_stats.top_moves == 1
    
    def test_game_analysis_to_dict(self):
        """Test GameAnalysis serialization."""
        # Create a simple game
        pgn = StringIO("1. e4 e5")
        game = chess.pgn.read_game(pgn)
        
        # Create move assessments
        moves = [
            MoveAssessment(
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
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4 e5",
            game=game,
            moves=moves
        )
        
        result = game_analysis.to_dict()
        assert result["pgn"] == "1. e4 e5"
        assert result["total_moves"] == 1
        assert "white_stats" in result
        assert "black_stats" in result
        assert "game_accuracy" in result
        assert "overall_quality" in result
        assert len(result["moves"]) == 1


class TestAnalysisResult:
    """Test AnalysisResult class."""
    
    def test_analysis_result_creation(self):
        """Test AnalysisResult creation."""
        # Create a simple game analysis
        pgn = StringIO("1. e4 e5")
        game = chess.pgn.read_game(pgn)
        
        moves = [
            MoveAssessment(
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
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4 e5",
            game=game,
            moves=moves
        )
        
        analysis_result = AnalysisResult(games=[game_analysis])
        
        assert len(analysis_result.games) == 1
        assert analysis_result.total_games == 1
        assert analysis_result.total_moves == 1
    
    def test_analysis_result_to_dict(self):
        """Test AnalysisResult serialization."""
        # Create a simple game analysis
        pgn = StringIO("1. e4 e5")
        game = chess.pgn.read_game(pgn)
        
        moves = [
            MoveAssessment(
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
        ]
        
        game_analysis = GameAnalysis(
            pgn="1. e4 e5",
            game=game,
            moves=moves
        )
        
        analysis_result = AnalysisResult(games=[game_analysis])
        
        result = analysis_result.to_dict()
        assert result["total_games"] == 1
        assert result["total_moves"] == 1
        assert len(result["games"]) == 1


if __name__ == "__main__":
    pytest.main([__file__])
