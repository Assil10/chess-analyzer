"""
Configuration file for Chess Analysis AI.
"""

import os
from pathlib import Path

# Default analysis parameters
DEFAULT_SHALLOW_DEPTH = 10
DEFAULT_DEEP_DEPTH = 20
DEFAULT_MULTIPV = 3

# Move quality thresholds (in centipawns)
MOVE_THRESHOLDS = {
    "TOP": 20,           # ≤20 cp loss
    "EXCELLENT": 50,     # ≤50 cp loss
    "GOOD": 120,         # ≤120 cp loss
    "MISTAKE": 300,      # ≤300 cp loss
    "BLUNDER": float('inf')  # >300 cp loss
}

# Brilliant move detection parameters
BRILLIANT_PARAMS = {
    "CP_THRESHOLD": 30,           # Max cp loss for brilliant
    "ONLY_MOVE_EVAL_THRESHOLD": -200,  # Eval threshold for only move
    "SACRIFICE_MATERIAL_THRESHOLD": 300,  # Min material drop for sacrifice
    "WINNING_EVAL_THRESHOLD": 600,  # Eval threshold for "already winning"
}

# API configuration
API_CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 8000,
    "DEBUG": True,
    "RELOAD": True
}

# File paths
PROJECT_ROOT = Path(__file__).parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
TESTS_DIR = PROJECT_ROOT / "tests"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
        "chess_analyzer": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
    }
}

# Engine configuration
ENGINE_CONFIG = {
    "TIMEOUT": 30,  # seconds
    "MAX_DEPTH": 50,
    "DEFAULT_HASH_SIZE": 128,  # MB
}

# Output configuration
OUTPUT_CONFIG = {
    "DEFAULT_OUTPUT_DIR": PROJECT_ROOT / "output",
    "SUPPORTED_FORMATS": ["pgn", "json", "txt"],
    "MAX_GAMES_PER_BATCH": 100,
}

# Test configuration
TEST_CONFIG = {
    "MOCK_ENGINE": True,  # Use mock engine for tests
    "TEST_PGN_FILE": EXAMPLES_DIR / "sample_game.pgn",
    "COVERAGE_THRESHOLD": 80,  # Minimum test coverage percentage
}

def get_config():
    """Get configuration dictionary."""
    return {
        "defaults": {
            "shallow_depth": DEFAULT_SHALLOW_DEPTH,
            "deep_depth": DEFAULT_DEEP_DEPTH,
            "multipv": DEFAULT_MULTIPV,
        },
        "thresholds": MOVE_THRESHOLDS,
        "brilliant": BRILLIANT_PARAMS,
        "api": API_CONFIG,
        "engine": ENGINE_CONFIG,
        "output": OUTPUT_CONFIG,
        "test": TEST_CONFIG,
        "logging": LOGGING_CONFIG,
    }

def create_output_directory():
    """Create output directory if it doesn't exist."""
    output_dir = OUTPUT_CONFIG["DEFAULT_OUTPUT_DIR"]
    output_dir.mkdir(exist_ok=True)
    return output_dir

def get_sample_pgn_path():
    """Get path to sample PGN file."""
    return TEST_CONFIG["TEST_PGN_FILE"]

def is_test_mode():
    """Check if running in test mode."""
    return os.getenv("CHESS_ANALYSIS_TEST", "false").lower() == "true"
