"""
Move evaluation logic for chess analysis (Chess.com-style, tuned).
"""

import chess
import chess.pgn
from typing import List, Tuple
from .models import MoveAssessment, MoveLabel
from .engine import ChessEngine
import logging

logger = logging.getLogger(__name__)


class MoveEvaluator:
    """Evaluates chess moves using Stockfish engine analysis in a Chess.com-like style."""

    def __init__(self, chess_engine: ChessEngine):
        self.engine = chess_engine

        # Tunable thresholds (centipawns) – stricter like Chess.com
        self.CP_LOSS_CLAMP = 1000              # cap extreme swings (mates etc.)

        self.GREAT_MAX = 5                     # Great: ≤ 5 cp (very rare, almost perfect)
        self.EXCELLENT_MAX = 15                # Excellent: ≤ 15 cp
        self.GOOD_MAX = 40                     # Good: ≤ 40 cp
        self.INACC_MAX = 100                   # Inaccuracy: ≤ 100 cp
        self.MISTAKE_MAX = 200                 # Mistake: ≤ 200 cp
        self.MISS_MIN = 201                    # Missed chance (201–400)
        self.MISS_MAX = 400
        self.BLUNDER_MIN = 401                 # Blunder: > 400 cp

        # Game-context constraints
        self.BRILLIANT_CAP = 2                 # max brilliant per game
        self.brilliant_count = 0

        # “Only move” detection helper
        self.only_move_eval_threshold = -200

    # ---------- Public API ----------

    def evaluate_move(
        self,
        board: chess.Board,
        move: chess.Move,
        shallow_depth: int = 10,
        deep_depth: int = 20,
        multipv: int = 3
    ) -> MoveAssessment:
        # Snapshot before move
        board_before = board.copy()
        move_san = board_before.san(move)
        side_to_move_is_white = board_before.turn

        # Eval before and top moves (before the move)
        eval_before = self.engine.get_evaluation(board_before, shallow_depth)
        shallow_moves = self.engine.get_top_moves(board_before, shallow_depth, multipv)

        # Make the move and eval after
        board_after = board_before.copy()
        board_after.push(move)
        eval_after = self.engine.get_evaluation(board_after, shallow_depth)

        # Deep moves after (for surprise/brilliant checks)
        deep_moves = self.engine.get_top_moves(board_after, deep_depth, multipv)

        # Determine best-eval-after (from the pre-move PV)
        if shallow_moves:
            best_eval_after = shallow_moves[0][1]
            best_move_san = shallow_moves[0][0]
        else:
            # Fallback: if we didn't get multipv, treat our move as baseline
            best_eval_after = eval_after
            best_move_san = move_san

        # Core: loss vs best (ALWAYS from after-positions)
        raw_loss = abs(best_eval_after - eval_after)
        loss_vs_best = int(min(raw_loss, self.CP_LOSS_CLAMP))

        # Other features
        is_book = self._detect_book_move(board_before, move)
        is_only_move = self._detect_only_move(board_before, eval_before)
        is_sacrifice = self._detect_sacrifice(board_before, move, eval_before, eval_after)
        is_surprise = self._detect_surprise(shallow_moves, deep_moves, move_san)

        # Missed-tactic detection (Chess.com-style “Miss”)
        is_miss = self._detect_miss(
            eval_before=eval_before,
            best_eval_after=best_eval_after,
            eval_after=eval_after,
            side_to_move_is_white=side_to_move_is_white,
            loss_vs_best=loss_vs_best
        )

        # Brilliant (rare) – limited per game
        is_brilliant = False
        if self.brilliant_count < self.BRILLIANT_CAP:
            is_brilliant = self._detect_brilliant(
                loss_vs_best=loss_vs_best,
                eval_before=eval_before,
                is_only_move=is_only_move,
                is_sacrifice=is_sacrifice,
                is_surprise=is_surprise
            )
            if is_brilliant:
                self.brilliant_count += 1

        # Final label
        label = self.get_move_label(
            loss_vs_best=loss_vs_best,
            is_brilliant=is_brilliant,
            is_book=is_book,
            is_miss=is_miss,
            eval_before=eval_before
        )

        # Build assessment
        return MoveAssessment(
            move=move_san,
            move_number=len(board.move_stack) + 1,
            is_white=board.turn,  # side who is about to move (the player who just played)
            san=move_san,
            uci=move.uci(),
            cp_gain=eval_after - eval_before,
            loss_vs_best=loss_vs_best,
            best_move=best_move_san,
            label=label,
            brilliant=is_brilliant,
            is_only_move=is_only_move,
            is_sacrifice=is_sacrifice,
            is_surprise=is_surprise,
            eval_before=eval_before,
            eval_after=eval_after,
            material_change=self._calculate_material_change(board_before, move),
            shallow_depth=shallow_depth,
            deep_depth=deep_depth,
            multipv_count=multipv
        )

    # ---------- Labeling ----------

    def get_move_label(
        self,
        loss_vs_best: int,
        is_brilliant: bool = False,
        is_book: bool = False,
        is_miss: bool = False,
        eval_before: int = 0
    ) -> MoveLabel:
        """Map to Chess.com-like labels with stricter thresholds and context-aware blunders."""
        if is_book:
            return MoveLabel.BOOK
        if is_brilliant:
            return MoveLabel.BRILLIANT
        if loss_vs_best == 0:
            return MoveLabel.BEST_MOVE
        if is_miss:
            return MoveLabel.MISS
        if loss_vs_best <= self.GREAT_MAX:
            return MoveLabel.GREAT_MOVE
        if loss_vs_best <= self.EXCELLENT_MAX:
            return MoveLabel.EXCELLENT
        if loss_vs_best <= self.GOOD_MAX:
            return MoveLabel.GOOD
        if loss_vs_best <= self.INACC_MAX:
            return MoveLabel.INACCURACY
        if loss_vs_best <= self.MISTAKE_MAX:
            return MoveLabel.MISTAKE
        if self.MISS_MIN <= loss_vs_best <= self.MISS_MAX:
            return MoveLabel.MISS

        # Blunder context: avoid flooding already lost/won positions with blunders
        eval_pawns = eval_before / 100.0
        if abs(eval_pawns) >= 3.0:  # already ±3 pawns (decided)
            return MoveLabel.MISTAKE if loss_vs_best < self.BLUNDER_MIN else MoveLabel.BLUNDER

        return MoveLabel.BLUNDER

    # ---------- Heuristics ----------

    def _detect_only_move(self, board: chess.Board, eval_before: int) -> bool:
        if eval_before <= self.only_move_eval_threshold:
            legal = list(board.legal_moves)
            return len(legal) == 1
        return False

    def _detect_sacrifice(
        self, board: chess.Board, move: chess.Move, eval_before: int, eval_after: int
    ) -> bool:
        """Material sacrifice that doesn't tank eval → candidate for brilliant."""
        material_change = self._calculate_material_change(board, move)  # after - before
        if material_change < -3:  # gave up ≥ a minor piece (3 pawns)
            # eval didn't collapse massively
            if (eval_after - eval_before) > -300:
                return True
        return False

    def _detect_book_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Book only if found in polyglot within first 8 full moves (16 plies)."""
        if len(board.move_stack) >= 16:
            return False
        try:
            import chess.polyglot
            for book_file in ("data/gm2600.bin", "data/performance.bin", "data/eco.bin"):
                try:
                    with chess.polyglot.open_reader(book_file) as reader:
                        for entry in reader.find_all(board):
                            if entry.move == move:
                                return True
                except FileNotFoundError:
                    continue
        except ImportError:
            pass
        return False

    def _detect_surprise(
        self,
        shallow_moves: List[Tuple[str, int, str]],
        deep_moves: List[Tuple[str, int, str]],
        played_move_san: str
    ) -> bool:
        """Not in shallow top-N but becomes best after deeper search."""
        if not shallow_moves or not deep_moves:
            return False
        shallow_sans = [m[0] for m in shallow_moves]
        if played_move_san in shallow_sans:
            return False
        return deep_moves[0][0] == played_move_san

    def _detect_brilliant(
        self,
        loss_vs_best: int,
        eval_before: int,
        is_only_move: bool,
        is_sacrifice: bool,
        is_surprise: bool
    ) -> bool:
        # Require sacrifice OR surprise, near-best eval, and not trivially winning/losing
        if not (is_sacrifice or is_surprise):
            return False
        if not (0 <= loss_vs_best <= 20):  # tighter brilliant window
            return False
        if eval_before > 150 or eval_before < -200:
            return False
        if is_only_move:
            return False
        return True

    def _detect_miss(
        self,
        eval_before: int,
        best_eval_after: int,
        eval_after: int,
        side_to_move_is_white: bool,
        loss_vs_best: int
    ) -> bool:
        """
        A 'Miss' is when there was a big improvement available, but the player
        chose a reasonable move that didn’t find it (not a blunder).
        """
        if side_to_move_is_white:
            best_gain = best_eval_after - eval_before
            played_gain = eval_after - eval_before
        else:
            best_gain = eval_before - best_eval_after
            played_gain = eval_before - eval_after

        big_chance = best_gain >= 300  # missed ≥ 3 pawns of improvement
        reasonable = 20 <= loss_vs_best <= 150  # Use fixed value instead of MISS_MAX
        return big_chance and reasonable

    # ---------- Material helpers ----------

    def _calculate_material_change(self, board: chess.Board, move: chess.Move) -> int:
        """Return material change (after - before) in pawn units, white-positive."""
        before = self._material_value(board)
        after_board = board.copy()
        after_board.push(move)
        after = self._material_value(after_board)
        return after - before

    def _material_value(self, board: chess.Board) -> int:
        values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
        total = 0
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p:
                val = values[p.piece_type]
                total += val if p.color == chess.WHITE else -val
        return total

    def evaluate_game(
        self,
        game: chess.pgn.Game,
        shallow_depth: int = 10,
        deep_depth: int = 20,
        multipv: int = 3
    ) -> List[MoveAssessment]:
        """Evaluate all moves in a chess game."""
        # Reset per-game counters
        self.brilliant_count = 0
        
        assessments: List[MoveAssessment] = []
        board = game.board()
        move_number = 1
        
        for node in game.mainline():
            if node.move:
                assessment = self.evaluate_move(board, node.move, shallow_depth, deep_depth, multipv)
                assessment.move_number = move_number
                assessment.is_white = board.turn
                assessments.append(assessment)
                board.push(node.move)
                move_number += 1
        
        return assessments
