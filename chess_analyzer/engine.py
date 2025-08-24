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
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to the chess engine."""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            logger.info(f"Connected to chess engine at {self.engine_path}")
        except Exception as e:
            logger.error(f"Failed to connect to chess engine: {e}")
            raise RuntimeError(f"Cannot connect to chess engine at {self.engine_path}")
    
    def _ensure_connected(self) -> None:
        """Ensure engine is connected, reconnect if necessary."""
        if self.engine is None or self.engine.is_terminated():
            logger.warning("Engine disconnected, attempting to reconnect...")
            self._connect()
    
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
        
        if multipv > 1:
            self.engine.configure({"MultiPV": multipv})
        
        try:
            if time_limit:
                result = self.engine.analyse(
                    board, 
                    chess.engine.Limit(time=time_limit),
                    multipv=multipv
                )
            else:
                result = self.engine.analyse(
                    board, 
                    chess.engine.Limit(depth=depth),
                    multipv=multipv
                )
            
            # Handle single vs multiple PV results
            if multipv == 1:
                return [result]
            else:
                return result
                
        except Exception as e:
            logger.error(f"Engine analysis failed: {e}")
            raise RuntimeError(f"Engine analysis failed: {e}")
    
    def get_evaluation(self, board: chess.Board, depth: int = 10) -> int:
        """
        Get simple evaluation of a position.
        
        Args:
            board: Chess position
            depth: Analysis depth
            
        Returns:
            Evaluation in centipawns (positive = white advantage)
        """
        result = self.analyze_position(board, depth, multipv=1)[0]
        
        if "score" in result:
            score = result["score"]
            if score.is_mate():
                # Convert mate to large centipawn value
                if score.mate() > 0:
                    return 10000  # White mates
                else:
                    return -10000  # Black mates
            else:
                return score.score()
        else:
            return 0
    
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
        results = self.analyze_position(board, depth, multipv=count)
        
        top_moves = []
        for result in results:
            if "pv" in result and "score" in result:
                move = result["pv"][0] if result["pv"] else None
                if move:
                    # Convert UCI move to SAN
                    san = board.san(move)
                    uci = move.uci()
                    
                    # Get evaluation
                    score = result["score"]
                    if score.is_mate():
                        eval_cp = 10000 if score.mate() > 0 else -10000
                    else:
                        eval_cp = score.score()
                    
                    top_moves.append((san, eval_cp, uci))
        
        return top_moves
    
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
    
    def close(self) -> None:
        """Close the engine connection."""
        if self.engine and not self.engine.is_terminated():
            self.engine.quit()
            logger.info("Chess engine connection closed")
    
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
