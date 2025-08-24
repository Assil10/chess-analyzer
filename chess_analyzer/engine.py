"""
Chess engine wrapper for Stockfish UCI communication.
"""

import chess
import chess.engine
import chess.pgn
from typing import List, Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ChessEngine:
    """Wrapper for Stockfish chess engine with analysis capabilities."""
    
    def __init__(self, engine_path: str):
        """
        Initialize the chess engine.
        
        Args:
            engine_path: Path to Stockfish executable
        """
        self.engine_path = engine_path
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.analysis_timeout = 30.0  # Default timeout in seconds
        self._connect()
    
    def set_timeout(self, timeout: float) -> None:
        """
        Set the analysis timeout.
        
        Args:
            timeout: Timeout in seconds
        """
        self.analysis_timeout = timeout
        logger.info(f"Analysis timeout set to {timeout} seconds")
    
    def _connect(self) -> None:
        """Establish connection to the chess engine."""
        try:
            if self.engine:
                try:
                    self.engine.quit()
                except:
                    pass
                self.engine = None
            
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            
            # Set some basic engine options for stability
            try:
                # Configure engine for analysis
                self.engine.configure({
                    "Threads": 1,
                    "Hash": 16,
                    "MultiPV": 1,  # Default MultiPV setting
                    "UCI_Chess960": False,
                    "UCI_AnalyseMode": True
                })
                logger.info("Engine configured successfully")
            except Exception as config_error:
                logger.warning(f"Engine configuration failed (non-critical): {config_error}")
                # Continue without configuration
            
            logger.info(f"Connected to chess engine at {self.engine_path}")
        except Exception as e:
            logger.error(f"Failed to connect to chess engine: {e}")
            raise RuntimeError(f"Cannot connect to chess engine at {self.engine_path}")
    
    def reset_engine(self) -> None:
        """Reset the engine connection if it's in a bad state."""
        logger.info("Resetting chess engine connection")
        self._connect()
    
    def _ensure_connected(self):
        """Ensure engine is connected and ready."""
        if self.engine is None:
            self._connect()
        
        # Try to ping the engine to see if it's responsive
        try:
            # Simple test to see if engine is responsive
            test_board = chess.Board()
            self.engine.analyse(test_board, chess.engine.Limit(depth=1), multipv=1)
        except Exception as e:
            logger.warning(f"Engine not responsive, resetting: {e}")
            self.reset_engine()
    
    def _validate_board_state(self, board: chess.Board) -> bool:
        """
        Validate that the board is in a legal state.
        
        Args:
            board: Chess board to validate
            
        Returns:
            True if board is valid, False otherwise
        """
        try:
            # Check if the board is valid
            if not board.is_valid():
                return False
            
            # Check if the current position is legal
            if board.is_checkmate() or board.is_stalemate() or board.is_insufficient_material():
                return True  # These are valid terminal positions
            
            # Check if there are any legal moves (for non-terminal positions)
            if not board.is_game_over():
                legal_moves = list(board.legal_moves)
                if len(legal_moves) == 0:
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Board validation failed: {e}")
            return False
    
    def _safe_analyze(self, board: chess.Board, limit: chess.engine.Limit, multipv: int = 1):
        """Safely analyze a position with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.engine.analyse(board, limit, multipv=multipv)
                return result
            except chess.engine.EngineError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Engine error on attempt {attempt + 1}, retrying: {e}")
                    self.reset_engine()
                    continue
                else:
                    logger.error(f"Engine error on final attempt: {e}")
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Unexpected error on attempt {attempt + 1}, retrying: {e}")
                    self.reset_engine()
                    continue
                else:
                    logger.error(f"Unexpected error on final attempt: {e}")
                    raise
    
    def analyze_position(
        self, 
        board: chess.Board, 
        depth: int, 
        multipv: int = 1,
        time_limit: Optional[float] = None
    ) -> List[chess.engine.InfoDict]:
        """
        Analyze a chess position.
        
        Args:
            board: Chess position to analyze
            depth: Analysis depth
            multipv: Number of top moves to analyze
            time_limit: Time limit in seconds (optional)
            
        Returns:
            List of analysis results for top moves
        """
        self._ensure_connected()
        
        # Validate board state before analysis
        if not self._validate_board_state(board):
            logger.warning("Invalid board state, returning empty result")
            return []
        
        # MultiPV is automatically managed in newer python-chess versions
        # No need to configure it manually
        
        try:
            # Set a reasonable time limit if none provided
            if not time_limit:
                time_limit = min(depth * 0.1, self.analysis_timeout)
            
            logger.debug(f"Analyzing position at depth {depth}, multipv {multipv}, timeout {time_limit}s")
            
            # Use the safer analysis method
            result = self._safe_analyze(
                board, 
                chess.engine.Limit(depth=depth, time=time_limit),
                multipv=multipv
            )
            
            # Handle single vs multiple PV results
            if multipv == 1:
                return [result]
            else:
                return result
                
        except chess.engine.EngineError as e:
            logger.error(f"Engine analysis failed: {e}")
            # Return empty result on engine error
            return []
        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}")
            # Return empty result on other errors
            return []
    
    def get_evaluation(self, board: chess.Board, depth: int = 10) -> int:
        """
        Get simple evaluation of a position.
        
        Args:
            board: Chess position
            depth: Analysis depth
            
        Returns:
            Evaluation in centipawns (positive = white advantage)
        """
        try:
            result = self.analyze_position(board, depth, multipv=1)
            if not result:
                logger.warning("No analysis result returned, using material evaluation")
                return self._calculate_material_evaluation(board)
            
            # Handle nested list structure: [[{...}]] -> [{...}]
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], list) and len(result[0]) > 0:
                    result = result[0][0]  # Handle [[{...}]] case
                else:
                    result = result[0]  # Handle [{...}] case
            else:
                logger.warning("Unexpected result structure, using material evaluation")
                return self._calculate_material_evaluation(board)
            
            if isinstance(result, dict) and "score" in result:
                score = result["score"]
                
                if score.is_mate():
                    # For PovScore, get the mate value from white's perspective
                    if hasattr(score, 'white'):
                        white_score = score.white()
                        if white_score.is_mate():
                            mate_value = white_score.mate()
                            return 10000 if mate_value > 0 else -10000
                    # Fallback for other score types
                    return 10000 if score.mate() > 0 else -10000
                else:
                    # Handle PovScore objects from newer python-chess versions
                    if hasattr(score, 'white'):
                        eval_cp = score.white().score(mate_score=10000)
                        return eval_cp
                    else:
                        eval_cp = score.score()
                        return eval_cp
            else:
                logger.warning("No score in analysis result, using material evaluation")
                return self._calculate_material_evaluation(board)
        except Exception as e:
            logger.error(f"Failed to get evaluation: {e}, using material evaluation")
            return self._calculate_material_evaluation(board)
    
    def _calculate_material_evaluation(self, board: chess.Board) -> int:
        """
        Calculate simple material-based evaluation as fallback.
        
        Args:
            board: Chess position
            
        Returns:
            Material evaluation in centipawns
        """
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
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
        
        return total_value
    
    def get_top_moves(
        self, 
        board: chess.Board, 
        depth: int, 
        count: int = 3
    ) -> List[Tuple[str, int, str]]:
        """
        Get top moves for a position.
        
        Args:
            board: Chess position
            depth: Analysis depth
            count: Number of top moves to return
            
        Returns:
            List of (move_san, evaluation, move_uci) tuples
        """
        try:
            # Create a copy of the board to avoid modifying the original
            board_copy = board.copy()
            
            results = self.analyze_position(board_copy, depth, multipv=count)
            
            # Handle nested list structure: [[{...}]] -> [{...}]
            if isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], list) and len(results[0]) > 0:
                    results = results[0]  # Handle [[{...}]] case
                # Otherwise keep as [{...}]
            
            top_moves = []
            for result in results:
                if isinstance(result, dict) and "pv" in result and "score" in result:
                    move = result["pv"][0] if result["pv"] else None
                    if move:
                        try:
                            # Check if the move is legal on the board copy
                            if move not in board_copy.legal_moves:
                                logger.warning(f"Move {move} is not legal on board, skipping")
                                continue
                            
                            # Convert UCI move to SAN safely
                            san = board_copy.san(move)
                            uci = move.uci()
                            
                            # Get evaluation
                            score = result["score"]
                            
                            if score.is_mate():
                                # For PovScore, get the mate value from white's perspective
                                if hasattr(score, 'white'):
                                    white_score = score.white()
                                    if white_score.is_mate():
                                        mate_value = white_score.mate()
                                        eval_cp = 10000 if mate_value > 0 else -10000
                                    else:
                                        eval_cp = white_score.score(mate_score=10000)
                                else:
                                    # Fallback for other score types
                                    eval_cp = 10000 if score.mate() > 0 else -10000
                            else:
                                # Handle PovScore objects from newer python-chess versions
                                if hasattr(score, 'white'):
                                    eval_cp = score.white().score(mate_score=10000)
                                else:
                                    eval_cp = score.score()
                            
                            top_moves.append((san, eval_cp, uci))
                        except Exception as e:
                            logger.warning(f"Failed to process move {move}: {e}")
                            continue
            
            return top_moves
        except Exception as e:
            logger.error(f"Failed to get top moves: {e}")
            # Return empty list on error
            return []
    
    def analyze_move_sequence(
        self, 
        board: chess.Board, 
        moves: List[chess.Move], 
        depth: int = 10
    ) -> List[Tuple[chess.Move, int]]:
        """
        Analyze a sequence of moves.
        
        Args:
            board: Starting position
            moves: List of moves to analyze
            depth: Analysis depth
            
        Returns:
            List of (move, evaluation) tuples
        """
        evaluations = []
        current_board = board.copy()
        
        for move in moves:
            # Analyze position before move
            eval_before = self.get_evaluation(current_board, depth)
            
            # Make move
            current_board.push(move)
            
            # Analyze position after move
            eval_after = self.get_evaluation(current_board, depth)
            
            evaluations.append((move, eval_before, eval_after))
        
        return evaluations
    
    def close(self):
        """Close the engine connection."""
        if self.engine:
            try:
                self.engine.quit()
            except Exception as e:
                logger.warning(f"Error closing engine: {e}")
            finally:
                self.engine = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor to ensure engine is closed."""
        try:
            self.close()
        except:
            pass
