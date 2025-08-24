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
    """Evaluates chess moves and detects brilliant moves."""
    
    def __init__(self, engine: ChessEngine):
        """
        Initialize the move evaluator.
        
        Args:
            engine: Chess engine instance
        """
        self.engine = engine
        
        # Centipawn loss thresholds for move labeling
        self.thresholds = {
            MoveLabel.TOP: 20,
            MoveLabel.EXCELLENT: 50,
            MoveLabel.GOOD: 120,
            MoveLabel.MISTAKE: 300,
            MoveLabel.BLUNDER: float('inf')
        }
        
        # Brilliant move detection parameters
        self.brilliant_cp_threshold = 30  # Max cp loss for brilliant
        self.only_move_eval_threshold = -200  # Eval threshold for only move
        self.sacrifice_material_threshold = 300  # Min material drop for sacrifice
        self.winning_eval_threshold = 600  # Eval threshold for "already winning"
    
    def evaluate_move(
        self,
        board: chess.Board,
        move: chess.Move,
        move_number: int,
        is_white: bool,
        shallow_depth: int = 10,
        deep_depth: int = 20,
        multipv: int = 3
    ) -> MoveAssessment:
        """
        Evaluate a single chess move.
        
        Args:
            board: Position before the move
            move: Move to evaluate
            move_number: Move number in the game
            is_white: Whether the move is by white
            shallow_depth: Depth for shallow analysis
            deep_depth: Depth for deep analysis
            multipv: Number of top moves to analyze
            
        Returns:
            MoveAssessment object with evaluation results
        """
        # Get evaluation before move
        eval_before = self.engine.get_evaluation(board, shallow_depth)
        
        # Make move
        board_after = board.copy()
        board_after.push(move)
        eval_after = self.engine.get_evaluation(board_after, shallow_depth)
        
        # Calculate centipawn gain/loss
        cp_gain = eval_after - eval_before
        
        # Get top moves at shallow depth
        shallow_top_moves = self.engine.get_top_moves(board, shallow_depth, multipv)
        
        # Get top moves at deep depth
        deep_top_moves = self.engine.get_top_moves(board, deep_depth, multipv)
        
        # Find the played move in shallow analysis
        played_move_san = board.san(move)
        played_move_uci = move.uci()
        
        # Find best move and calculate loss vs best
        best_move_san = shallow_top_moves[0][0] if shallow_top_moves else "unknown"
        best_move_eval = shallow_top_moves[0][1] if shallow_top_moves else 0
        
        # Calculate loss vs best move
        if best_move_san == played_move_san:
            loss_vs_best = 0
        else:
            # Find played move in shallow analysis
            played_move_found = False
            for san, eval_cp, uci in shallow_top_moves:
                if san == played_move_san:
                    loss_vs_best = best_move_eval - eval_cp
                    played_move_found = True
                    break
            
            if not played_move_found:
                # Move not in top moves, estimate loss
                loss_vs_best = 500  # Conservative estimate
        
        # Determine move label based on centipawn loss
        label = self._get_move_label(loss_vs_best)
        
        # Detect heuristics
        is_only_move = self._detect_only_move(board, eval_before)
        is_sacrifice = self._detect_sacrifice(board, move, eval_before, eval_after)
        is_surprise = self._detect_surprise(shallow_top_moves, deep_top_moves, played_move_san)
        
        # Determine if move is brilliant
        brilliant = self._detect_brilliant(
            loss_vs_best, eval_before, is_only_move, is_sacrifice, is_surprise
        )
        
        # Calculate material change
        material_change = self._calculate_material_change(board, move)
        
        return MoveAssessment(
            move=played_move_san,
            move_number=move_number,
            is_white=is_white,
            san=played_move_san,
            uci=played_move_uci,
            cp_gain=cp_gain,
            loss_vs_best=loss_vs_best,
            best_move=best_move_san,
            label=label,
            brilliant=brilliant,
            is_only_move=is_only_move,
            is_sacrifice=is_sacrifice,
            is_surprise=is_surprise,
            eval_before=eval_before,
            eval_after=eval_after,
            material_change=material_change,
            shallow_depth=shallow_depth,
            deep_depth=deep_depth,
            multipv_count=multipv
        )
    
    def _get_move_label(self, loss_vs_best: int) -> MoveLabel:
        """Determine move label based on centipawn loss."""
        for label, threshold in self.thresholds.items():
            if loss_vs_best <= threshold:
                return label
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
    
    def _detect_sacrifice(self, board: chess.Board, move: chess.Move, eval_before: int, eval_after: int) -> bool:
        """Detect if move involves a material sacrifice but eval doesn't collapse."""
        # Calculate material value before and after
        material_before = self._calculate_material_value(board)
        
        board_after = board.copy()
        board_after.push(move)
        material_after = self._calculate_material_value(board_after)
        
        material_drop = material_before - material_after
        
        # Check if material drop is significant
        if material_drop >= self.sacrifice_material_threshold:
            # Check if eval doesn't collapse (stays within reasonable range)
            eval_change = eval_after - eval_before
            eval_threshold = -200  # Allow some eval drop but not too much
            
            return eval_change > eval_threshold
        
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
        near_best = loss_vs_best <= self.brilliant_cp_threshold
        
        # Check if position wasn't already winning
        not_already_winning = eval_before <= self.winning_eval_threshold
        
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
    
    def evaluate_game(self, game: chess.pgn.Game, shallow_depth: int = 10, 
                     deep_depth: int = 20, multipv: int = 3) -> List[MoveAssessment]:
        """
        Evaluate all moves in a chess game.
        
        Args:
            game: Chess game object
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
                is_white = board.turn == chess.WHITE
                
                assessment = self.evaluate_move(
                    board, node.move, move_number, is_white,
                    shallow_depth, deep_depth, multipv
                )
                
                assessments.append(assessment)
                
                # Make the move
                board.push(node.move)
                move_number += 1
        
        return assessments
