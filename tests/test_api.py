"""
Unit tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import chess.pgn
import json

from chess_analyzer.api import app, AnalysisRequest, AnalysisResponse


class TestAnalysisRequest:
    """Test AnalysisRequest model."""
    
    def test_analysis_request_creation(self):
        """Test creating AnalysisRequest instance."""
        request = AnalysisRequest(
            pgn="1. e4 e5",
            engine_path="/path/to/stockfish"
        )
        
        assert request.pgn == "1. e4 e5"
        assert request.engine_path == "/path/to/stockfish"
        assert request.shallow_depth == 10
        assert request.deep_depth == 20
        assert request.multipv == 3
    
    def test_analysis_request_custom_values(self):
        """Test AnalysisRequest with custom values."""
        request = AnalysisRequest(
            pgn="1. d4 d5",
            engine_path="/path/to/stockfish",
            shallow_depth=15,
            deep_depth=25,
            multipv=5
        )
        
        assert request.shallow_depth == 15
        assert request.deep_depth == 25
        assert request.multipv == 5


class TestAnalysisResponse:
    """Test AnalysisResponse model."""
    
    def test_analysis_response_success(self):
        """Test successful AnalysisResponse."""
        response = AnalysisResponse(
            success=True,
            message="Analysis completed",
            analysis={"moves": []},
            annotated_pgn="1. e4 {!! Brilliant}"
        )
        
        assert response.success is True
        assert response.message == "Analysis completed"
        assert response.analysis == {"moves": []}
        assert response.annotated_pgn == "1. e4 {!! Brilliant}"
        assert response.error is None
    
    def test_analysis_response_error(self):
        """Test error AnalysisResponse."""
        response = AnalysisResponse(
            success=False,
            message="Analysis failed",
            error="Engine not found"
        )
        
        assert response.success is False
        assert response.message == "Analysis failed"
        assert response.error == "Engine not found"
        assert response.analysis is None
        assert response.annotated_pgn is None


class TestAPIEndpoints:
    """Test FastAPI endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Chess Analysis AI API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chess-analysis-ai"
    
    def test_stats_endpoint(self):
        """Test stats endpoint."""
        response = self.client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "endpoints" in data
        assert "features" in data
        assert "move_labels" in data
    
    @patch('chess_analyzer.api.ChessEngine')
    @patch('chess_analyzer.api.MoveEvaluator')
    @patch('chess_analyzer.api.PGNAnnotator')
    def test_analyze_endpoint_success(self, mock_annotator, mock_evaluator, mock_engine):
        """Test successful analysis endpoint."""
        # Mock the analysis components
        mock_engine_instance = Mock()
        mock_engine_instance.get_evaluation.return_value = 0
        mock_engine_instance.get_top_moves.return_value = [("e4", 100, "e2e4")]
        mock_engine.return_value = mock_engine_instance
        
        mock_evaluator_instance = Mock()
        mock_evaluator_instance.evaluate_game.return_value = []
        mock_evaluator.return_value = mock_evaluator_instance
        
        mock_annotator_instance = Mock()
        mock_annotator_instance.annotate_game.return_value = "1. e4 {!! Brilliant}"
        mock_annotator.return_value = mock_annotator_instance
        
        # Test request
        request_data = {
            "pgn": "1. e4",
            "engine_path": "/path/to/stockfish",
            "shallow_depth": 10,
            "deep_depth": 20,
            "multipv": 3
        }
        
        response = self.client.post("/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Game analyzed successfully" in data["message"]
        assert data["annotated_pgn"] == "1. e4 {!! Brilliant}"
    
    def test_analyze_endpoint_invalid_pgn(self):
        """Test analysis endpoint with invalid PGN."""
        request_data = {
            "pgn": "invalid pgn",
            "engine_path": "/path/to/stockfish"
        }
        
        response = self.client.post("/analyze", json=request_data)
        assert response.status_code == 200  # API returns 200 with error in response
        
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    def test_analyze_endpoint_missing_required_fields(self):
        """Test analysis endpoint with missing required fields."""
        request_data = {
            "pgn": "1. e4"
            # Missing engine_path
        }
        
        response = self.client.post("/analyze", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @patch('chess_analyzer.api.ChessEngine')
    def test_analyze_endpoint_engine_error(self, mock_engine):
        """Test analysis endpoint when engine fails."""
        mock_engine.side_effect = RuntimeError("Engine not found")
        
        request_data = {
            "pgn": "1. e4",
            "engine_path": "/invalid/path"
        }
        
        response = self.client.post("/analyze", json=request_data)
        assert response.status_code == 200  # API returns 200 with error in response
        
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    @patch('chess_analyzer.api.ChessEngine')
    @patch('chess_analyzer.api.MoveEvaluator')
    @patch('chess_analyzer.api.PGNAnnotator')
    def test_analyze_file_endpoint_success(self, mock_annotator, mock_evaluator, mock_engine):
        """Test successful file analysis endpoint."""
        # Mock the analysis components
        mock_engine_instance = Mock()
        mock_engine_instance.get_evaluation.return_value = 0
        mock_engine_instance.get_top_moves.return_value = [("e4", 100, "e2e4")]
        mock_engine.return_value = mock_engine_instance
        
        mock_evaluator_instance = Mock()
        mock_evaluator_instance.evaluate_game.return_value = []
        mock_evaluator.return_value = mock_evaluator_instance
        
        mock_annotator_instance = Mock()
        mock_annotator_instance.annotate_game.return_value = "1. e4 {!! Brilliant}"
        mock_annotator.return_value = mock_annotator_instance
        
        # Create test file content
        file_content = b"1. e4"
        
        # Test request
        response = self.client.post(
            "/analyze-file",
            files={"file": ("test.pgn", file_content, "text/plain")},
            data={
                "engine_path": "/path/to/stockfish",
                "shallow_depth": "10",
                "deep_depth": "20",
                "multipv": "3"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Game analyzed successfully" in data["message"]
        assert data["annotated_pgn"] == "1. e4 {!! Brilliant}"
    
    def test_analyze_file_endpoint_missing_file(self):
        """Test file analysis endpoint with missing file."""
        response = self.client.post(
            "/analyze-file",
            data={"engine_path": "/path/to/stockfish"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('chess_analyzer.api.ChessEngine')
    @patch('chess_analyzer.api.MoveEvaluator')
    @patch('chess_analyzer.api.PGNAnnotator')
    def test_analyze_batch_endpoint_success(self, mock_annotator, mock_evaluator, mock_engine):
        """Test successful batch analysis endpoint."""
        # Mock the analysis components
        mock_engine_instance = Mock()
        mock_engine_instance.get_evaluation.return_value = 0
        mock_engine_instance.get_top_moves.return_value = [("e4", 100, "e2e4")]
        mock_engine.return_value = mock_engine_instance
        
        mock_evaluator_instance = Mock()
        mock_evaluator_instance.evaluate_game.return_value = []
        mock_evaluator.return_value = mock_evaluator_instance
        
        mock_annotator_instance = Mock()
        mock_annotator_instance.annotate_game.return_value = "1. e4"
        mock_annotator_instance.batch_annotate_games.return_value = ["1. e4", "1. d4"]
        mock_annotator_instance.create_batch_summary.return_value = "Batch Summary"
        mock_annotator.return_value = mock_annotator_instance
        
        # Test request - send as form data since the endpoint expects both JSON and form
        response = self.client.post(
            "/analyze-batch",
            data={
                "pgn": "1. e4\n\n1. d4",
                "engine_path": "/path/to/stockfish",
                "shallow_depth": "10",
                "deep_depth": "20",
                "multipv": "3",
                "max_games": "5"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Successfully analyzed" in data["message"]
        assert "batch_analysis" in data
        assert "annotated_pgns" in data
        assert "summary" in data


if __name__ == "__main__":
    pytest.main([__file__])
