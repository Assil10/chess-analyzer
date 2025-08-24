"""
Move evaluation logic for chess analysis.
"""

import chess
import chess.pgn
from typing import List, Tuple, Optional, Dict, Any
from .models import MoveAssessment, MoveLabel
from .engine import ChessEngine
import logging

logger = logging.getLogger(__name__)


class MoveEvaluator:
    """Evaluates chess moves using Stockfish engine analysis."""
    
    def __init__(self, chess_engine: ChessEngine):
        """
        Initialize the move evaluator.
        
        Args:
            chess_engine: ChessEngine instance for analysis
        """
        self.engine = chess_engine
        self.sacrifice_material_threshold = 300  # 3 pawns
        self.only_move_eval_threshold = -200  # -200 centipawns
        self.brilliant_eval_threshold = 600  # +600 centipawns
        self.surprise_threshold = 0.3  # 30% of moves
    
    def evaluate_move(
        self, 
        board: chess.Board, 
        move: chess.Move, 
        shallow_depth: int = 10, 
        deep_depth: int = 20, 
        multipv: int = 3
    ) -> MoveAssessment:
        """
        Evaluate a single chess move.
        
        Args:
            board: Current board position
            move: Move to evaluate
            shallow_depth: Depth for shallow analysis
            deep_depth: Depth for deep analysis
            multipv: Number of top moves to analyze
            
        Returns:
            MoveAssessment object
        """
        # Create a copy of the board for analysis
        board_copy = board.copy()
        
        # Get the SAN notation before making the move
        move_san = board_copy.san(move)
        
        # Get evaluation before move
        eval_before = self.engine.get_evaluation(board_copy, shallow_depth)
        
        # Get top moves before the move
        shallow_moves = self.engine.get_top_moves(board_copy, shallow_depth, multipv)
        
        # Make the move on the copy
        board_copy.push(move)
        eval_after = self.engine.get_evaluation(board_copy, shallow_depth)
        
        # Get top moves after the move
        deep_moves = self.engine.get_top_moves(board_copy, deep_depth, multipv)
        
        # Calculate centipawn gain/loss
        cp_gain = eval_after - eval_before
        
        # Find the played move in the top moves
        played_move_rank = None
        loss_vs_best = 0
        
        for i, (san, eval_cp, uci) in enumerate(shallow_moves):
            if san == move_san:
                played_move_rank = i
                if i > 0:
                    # Calculate loss vs best move
                    best_move_eval = shallow_moves[0][1]
                    loss_vs_best = best_move_eval - eval_cp
                break
        
        # If move not found in top moves, it's a significant loss
        if played_move_rank is None:
            loss_vs_best = 500  # Significant loss
        
        # Detect heuristics
        is_only_move = self._detect_only_move(board, eval_before)
        is_sacrifice = self._detect_sacrifice(board, eval_before, eval_after)
        is_surprise = self._detect_surprise(shallow_moves, deep_moves, move_san)
        
        # Detect brilliant move
        is_brilliant = self._detect_brilliant(
            loss_vs_best, is_only_move, is_sacrifice, is_surprise, eval_before
        )
        
        # Detect book move (opening theory - first 10-15 moves)
        is_book = self._detect_book_move(board, move)
        
        # Determine move label based on centipawn loss
        label = self.get_move_label(loss_vs_best, is_brilliant, is_book)
        
        # Create move assessment
        assessment = MoveAssessment(
            move=move_san,
            move_number=len(board_copy.move_stack),
            is_white=board.turn,
            san=move_san,
            uci=move.uci(),
            cp_gain=cp_gain,
            loss_vs_best=loss_vs_best,
            best_move=shallow_moves[0][0] if shallow_moves else move_san,
            label=label,
            brilliant=is_brilliant,
            is_only_move=is_only_move,
            is_sacrifice=is_sacrifice,
            is_surprise=is_surprise,
            eval_before=eval_before,
            eval_after=eval_after,
            material_change=self._calculate_material_change(board, move),
            shallow_depth=shallow_depth,
            deep_depth=deep_depth,
            multipv_count=multipv
        )
        
        return assessment
    
    def get_move_label(self, loss_vs_best: int, is_brilliant: bool = False, is_book: bool = False) -> MoveLabel:
        """
        Get move label based on Chess.com classification system.
        
        Args:
            loss_vs_best: Centipawn loss compared to best move
            is_brilliant: Whether the move is marked as brilliant
            is_book: Whether the move is from opening theory
            
        Returns:
            MoveLabel classification
        """
        # Handle special cases first
        if is_brilliant:
            return MoveLabel.BRILLIANT
        
        if is_book:
            return MoveLabel.BOOK
        
        # Chess.com classification thresholds (approximate)
        if loss_vs_best == 0:
            return MoveLabel.BEST_MOVE
        elif loss_vs_best <= 10:
            return MoveLabel.GREAT_MOVE
        elif loss_vs_best <= 25:
            return MoveLabel.EXCELLENT
        elif loss_vs_best <= 50:
            return MoveLabel.GOOD
        elif loss_vs_best <= 100:
            return MoveLabel.INACCURACY
        elif loss_vs_best <= 200:
            return MoveLabel.MISTAKE
        else:
            return MoveLabel.BLUNDER
    
    def _detect_only_move(self, board: chess.Board, eval_before: int) -> bool:
        """Detect if this is the only legal move that keeps eval above threshold."""
        if eval_before <= self.only_move_eval_threshold:
            legal_moves = list(board.legal_moves)
            if len(legal_moves) == 1:
                return True
            
            # Check if only one move keeps eval above threshold
            moves_above_threshold = 0
            for move in legal_moves:
                board_copy = board.copy()
                board_copy.push(move)
                eval_after = self.engine.get_evaluation(board_copy, 5)  # Quick eval
                if eval_after > self.only_move_eval_threshold:
                    moves_above_threshold += 1
            
            return moves_above_threshold == 1
        
        return False
    
    def _detect_sacrifice(self, board: chess.Board, eval_before: int, eval_after: int) -> bool:
        """
        Detect if a move involves a material sacrifice.
        
        Args:
            board: Board after the move
            eval_before: Evaluation before the move
            eval_after: Evaluation after the move
            
        Returns:
            True if the move involves a sacrifice
        """
        # Check if there are any moves on the board
        if not board.move_stack:
            return False
            
        # Calculate material change
        material_change = self._calculate_material_change(board, board.peek())
        
        # Check if material was sacrificed (negative change)
        if material_change < -300:  # 3 pawns or more
            # Check if evaluation didn't collapse significantly
            eval_change = eval_after - eval_before
            if eval_change > -200:  # Evaluation didn't drop too much
                return True
        
        return False
    
    def _detect_book_move(self, board: chess.Board, move: chess.Move) -> bool:
        """
        Detect if a move is from opening theory (book move).
        
        Args:
            board: Current board position
            move: Move to check
            
        Returns:
            True if the move is likely from opening theory
        """
        # Consider first 15 moves as potential book moves
        if len(board.move_stack) < 15:
            # Check if the position is common in opening theory
            # This is a simplified heuristic - in practice, you'd use an opening database
            fen = board.fen().split(' ')[0]  # Get position part of FEN
            
            # Common opening positions (simplified)
            common_openings = [
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR",  # Starting position
                "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR",  # After 1.e4
                "rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR",  # After 1.e4 e5
                "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR",  # After 1.d4
                "rnbqkbnr/pppppppp/8/8/8/3P4/PPP1PPPP/RNBQKBNR",  # After 1.d4 d5
            ]
            
            if fen in common_openings:
                return True
            
            # Check if it's a standard developing move in the opening
            if len(board.move_stack) < 10:
                # Common developing moves
                if move.piece_type in [chess.KNIGHT, chess.BISHOP]:
                    return True
                if move.piece_type == chess.PAWN and move.from_square in [chess.E2, chess.E7, chess.D2, chess.D7]:
                    return True
        
        return False
    
    def _detect_surprise(self, shallow_moves: List[Tuple[str, int, str]], 
                         deep_moves: List[Tuple[str, int, str]], 
                         played_move: str) -> bool:
        """Detect if move is a surprise (not in shallow top-N but best at deep)."""
        if not shallow_moves or not deep_moves:
            return False
        
        # Check if played move is not in shallow top moves
        shallow_move_sans = [move[0] for move in shallow_moves]
        if played_move in shallow_move_sans:
            return False
        
        # Check if played move is best at deep analysis
        deep_best_move = deep_moves[0][0] if deep_moves else None
        return deep_best_move == played_move
    
    def _detect_brilliant(self, loss_vs_best: int, eval_before: int, 
                          is_only_move: bool, is_sacrifice: bool, is_surprise: bool) -> bool:
        """Determine if move should be marked as brilliant."""
        # Check if move is near-best
        near_best = loss_vs_best <= self.brilliant_eval_threshold
        
        # Check if position wasn't already winning
        not_already_winning = eval_before <= self.brilliant_eval_threshold
        
        # Check if move has one of the brilliant characteristics
        has_brilliant_characteristic = is_only_move or is_sacrifice or is_surprise
        
        return near_best and not_already_winning and has_brilliant_characteristic
    
    def _calculate_material_change(self, board: chess.Board, move: chess.Move) -> int:
        """Calculate material change caused by the move."""
        material_before = self._calculate_material_value(board)
        
        board_after = board.copy()
        board_after.push(move)
        material_after = self._calculate_material_value(board_after)
        
        return material_after - material_before
    
    def _calculate_material_value(self, board: chess.Board) -> int:
        """Calculate material value of a position in pawn units."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # King has no material value
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
    
    def evaluate_game(
        self, 
        game: chess.pgn.Game, 
        shallow_depth: int = 10, 
        deep_depth: int = 20, 
        multipv: int = 3
    ) -> List[MoveAssessment]:
        """
        Evaluate all moves in a chess game.
        
        Args:
            game: Chess game to evaluate
            shallow_depth: Depth for shallow analysis
            deep_depth: Depth for deep analysis
            multipv: Number of top moves to analyze
            
        Returns:
            List of MoveAssessment objects
        """
        assessments = []
        board = game.board()
        move_number = 1
        
        for node in game.mainline():
            if node.move:
                # Evaluate the move
                assessment = self.evaluate_move(
                    board, 
                    node.move, 
                    shallow_depth, 
                    deep_depth, 
                    multipv
                )
                
                # Update move number
                assessment.move_number = move_number
                assessment.is_white = board.turn
                
                assessments.append(assessment)
                move_number += 1
        
        return assessments
