"""
Unit tests for chess move evaluator.
"""

import pytest
from unittest.mock import Mock, MagicMock
import chess
import chess.pgn

from chess_analyzer.models import MoveLabel, MoveAssessment
from chess_analyzer.evaluator import MoveEvaluator


class MockChessEngine:
    """Mock chess engine for testing."""
    
    def __init__(self):
        self.engine = Mock()
    
    def get_evaluation(self, board, depth):
        """Mock evaluation method."""
        # Return a simple evaluation based on position
        if board.is_checkmate():
            return -10000 if board.turn else 10000
        elif board.is_stalemate():
            return 0
        else:
            # Simple material-based evaluation
            return self._calculate_material_eval(board)
    
    def get_top_moves(self, board, depth, count):
        """Mock top moves method."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return []
        
        # Return mock top moves
        moves = []
        for i, move in enumerate(legal_moves[:count]):
            san = board.san(move)
            eval_cp = 100 - i * 10  # Decreasing evaluation
            uci = move.uci()
            moves.append((san, eval_cp, uci))
        
        return moves
    
    def _calculate_material_eval(self, board):
        """Calculate simple material evaluation."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        total_value = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    total_value += value
                else:
                    total_value -= value
        
        return total_value * 100  # Convert to centipawns


class TestMoveEvaluator:
    """Test MoveEvaluator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = MockChessEngine()
        self.evaluator = MoveEvaluator(self.mock_engine)
    
    def test_evaluator_initialization(self):
        """Test MoveEvaluator initialization."""
        assert self.evaluator.engine == self.mock_engine
        assert self.evaluator.thresholds[MoveLabel.TOP] == 20
        assert self.evaluator.thresholds[MoveLabel.EXCELLENT] == 50
        assert self.evaluator.thresholds[MoveLabel.GOOD] == 120
        assert self.evaluator.thresholds[MoveLabel.MISTAKE] == 300
        assert self.evaluator.brilliant_cp_threshold == 30
    
    def test_get_move_label(self):
        """Test move label determination based on centipawn loss."""
        assert self.evaluator._get_move_label(0) == MoveLabel.TOP
        assert self.evaluator._get_move_label(20) == MoveLabel.TOP
        assert self.evaluator._get_move_label(25) == MoveLabel.EXCELLENT
        assert self.evaluator._get_move_label(50) == MoveLabel.EXCELLENT
        assert self.evaluator._get_move_label(75) == MoveLabel.GOOD
        assert self.evaluator._get_move_label(120) == MoveLabel.GOOD
        assert self.evaluator._get_move_label(200) == MoveLabel.MISTAKE
        assert self.evaluator._get_move_label(300) == MoveLabel.MISTAKE
        assert self.evaluator._get_move_label(400) == MoveLabel.BLUNDER
    
    def test_detect_only_move(self):
        """Test only move detection."""
        # Create a position with only one legal move
        board = chess.Board("8/8/8/8/8/8/8/K7 w - - 0 1")
        
        # This position has only one legal move (Ka1-b1 or similar)
        result = self.evaluator._detect_only_move(board, -300)
        assert result is True
        
        # Position with multiple moves
        board = chess.Board()
        result = self.evaluator._detect_only_move(board, 0)
        assert result is False
    
    def test_detect_sacrifice(self):
        """Test sacrifice detection."""
        # Create a position where a sacrifice might occur
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        move = chess.Move.from_uci("e2e4")
        
        # Test with no material change
        result = self.evaluator._detect_sacrifice(board, move, 0, 50)
        assert result is False
        
        # Test with material drop but eval improvement
        result = self.evaluator._detect_sacrifice(board, move, 0, 100)
        assert result is False  # No material drop in this case
    
    def test_detect_surprise(self):
        """Test surprise move detection."""
        # Mock top moves
        shallow_moves = [("e4", 100, "e2e4"), ("d4", 95, "d2d4"), ("Nf3", 90, "g1f3")]
        deep_moves = [("d4", 110, "d2d4"), ("e4", 105, "e2e4"), ("Nf3", 100, "g1f3")]
        
        # Test surprise (d4 not in shallow top 3 but best at deep)
        result = self.evaluator._detect_surprise(shallow_moves, deep_moves, "d4")
        assert result is True
        
        # Test no surprise (e4 is in both)
        result = self.evaluator._detect_surprise(shallow_moves, deep_moves, "e4")
        assert result is False
        
        # Test no surprise (move not in deep top)
        result = self.evaluator._detect_surprise(shallow_moves, deep_moves, "Nf3")
        assert result is False
    
    def test_detect_brilliant(self):
        """Test brilliant move detection."""
        # Test brilliant move (near-best + sacrifice)
        result = self.evaluator._detect_brilliant(
            loss_vs_best=25,  # Near-best
            eval_before=0,    # Not already winning
            is_only_move=False,
            is_sacrifice=True,  # Has brilliant characteristic
            is_surprise=False
        )
        assert result is True
        
        # Test not brilliant (too much loss)
        result = self.evaluator._detect_brilliant(
            loss_vs_best=50,  # Not near-best
            eval_before=0,
            is_only_move=False,
            is_sacrifice=True,
            is_surprise=False
        )
        assert result is False
        
        # Test not brilliant (already winning)
        result = self.evaluator._detect_brilliant(
            loss_vs_best=25,
            eval_before=800,  # Already winning
            is_only_move=False,
            is_sacrifice=True,
            is_surprise=False
        )
        assert result is False
        
        # Test not brilliant (no brilliant characteristic)
        result = self.evaluator._detect_brilliant(
            loss_vs_best=25,
            eval_before=0,
            is_only_move=False,
            is_sacrifice=False,
            is_surprise=False
        )
        assert result is False
    
    def test_calculate_material_value(self):
        """Test material value calculation."""
        # Starting position
        board = chess.Board()
        value = self.evaluator._calculate_material_value(board)
        assert value == 0  # Equal material
        
        # Position with white advantage
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        value = self.evaluator._calculate_material_value(board)
        assert value == 0  # Equal material
        
        # Position with black queen captured
        board = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        value = self.evaluator._calculate_material_value(board)
        assert value == 9  # White has +9 pawn advantage
    
    def test_calculate_material_change(self):
        """Test material change calculation."""
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        # No material change in this move
        change = self.evaluator._calculate_material_change(board, move)
        assert change == 0
    
    def test_evaluate_move(self):
        """Test complete move evaluation."""
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        
        assessment = self.evaluator.evaluate_move(
            board=board,
            move=move,
            move_number=1,
            is_white=True,
            shallow_depth=10,
            deep_depth=20,
            multipv=3
        )
        
        assert isinstance(assessment, MoveAssessment)
        assert assessment.move == "e4"
        assert assessment.move_number == 1
        assert assessment.is_white is True
        assert assessment.san == "e4"
        assert assessment.uci == "e2e4"
        assert assessment.label in [MoveLabel.TOP, MoveLabel.EXCELLENT, MoveLabel.GOOD, MoveLabel.MISTAKE, MoveLabel.BLUNDER]
        assert isinstance(assessment.brilliant, bool)
        assert isinstance(assessment.is_only_move, bool)
        assert isinstance(assessment.is_sacrifice, bool)
        assert isinstance(assessment.is_surprise, bool)
    
    def test_evaluate_game(self):
        """Test complete game evaluation."""
        # Create a simple game
        game = chess.pgn.Game()
        game.add_variation(chess.Move.from_uci("e2e4"))
        game.add_variation(chess.Move.from_uci("e7e5"))
        
        assessments = self.evaluator.evaluate_game(
            game=game,
            shallow_depth=10,
            deep_depth=20,
            multipv=3
        )
        
        assert len(assessments) == 2
        assert all(isinstance(a, MoveAssessment) for a in assessments)
        assert assessments[0].move_number == 1
        assert assessments[1].move_number == 2


if __name__ == "__main__":
    pytest.main([__file__])
