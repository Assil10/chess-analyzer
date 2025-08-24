"""
Chess Analysis AI - Top & Brilliant Move Detector

A Python project that analyzes chess games using Stockfish and labels moves
with quality assessments and brilliant move detection.
"""

__version__ = "1.0.0"
__author__ = "Chess Analysis AI Team"

from .models import MoveAssessment, GameAnalysis, AnalysisResult
from .engine import ChessEngine
from .evaluator import MoveEvaluator
from .annotator import PGNAnnotator

__all__ = [
    "MoveAssessment",
    "GameAnalysis", 
    "AnalysisResult",
    "ChessEngine",
    "MoveEvaluator",
    "PGNAnnotator",
]
