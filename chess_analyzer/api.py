"""
FastAPI endpoints for chess analysis.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import chess.pgn
import io
import logging

from .engine import ChessEngine
from .evaluator import MoveEvaluator
from .annotator import PGNAnnotator
from .models import GameAnalysis, AnalysisResult

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chess Analysis AI API",
    description="API for analyzing chess games with Stockfish and detecting brilliant moves",
    version="1.0.0"
)


class AnalysisRequest(BaseModel):
    """Request model for chess analysis."""
    pgn: str = Field(..., description="PGN string of the chess game")
    engine_path: str = Field(..., description="Path to Stockfish executable")
    shallow_depth: int = Field(default=10, description="Shallow analysis depth")
    deep_depth: int = Field(default=20, description="Deep analysis depth")
    multipv: int = Field(default=3, description="Number of top moves to analyze")


class AnalysisResponse(BaseModel):
    """Response model for chess analysis."""
    success: bool
    message: str
    analysis: Optional[Dict[str, Any]] = None
    annotated_pgn: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Chess Analysis AI API",
        "version": "1.0.0",
        "endpoints": {
            "/analyze": "POST - Analyze chess game from PGN string",
            "/analyze-file": "POST - Analyze chess game from uploaded PGN file",
            "/health": "GET - API health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chess-analysis-ai"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_game(request: AnalysisRequest):
    """
    Analyze a chess game from PGN string.
    
    Args:
        request: AnalysisRequest containing PGN and parameters
        
    Returns:
        AnalysisResponse with analysis results and annotated PGN
    """
    try:
        # Parse PGN
        pgn_io = io.StringIO(request.pgn)
        game = chess.pgn.read_game(pgn_io)
        
        if game is None:
            raise HTTPException(status_code=400, detail="Invalid PGN format")
        
        # Initialize engine and evaluator
        engine = ChessEngine(request.engine_path)
        evaluator = MoveEvaluator(engine)
        annotator = PGNAnnotator()
        
        try:
            # Evaluate the game
            move_assessments = evaluator.evaluate_game(
                game, 
                request.shallow_depth, 
                request.deep_depth, 
                request.multipv
            )
            
            # Create game analysis
            game_analysis = GameAnalysis(
                pgn=request.pgn,
                game=game,
                moves=move_assessments,
                total_moves=len(move_assessments)
            )
            
            # Annotate PGN
            annotated_pgn = annotator.annotate_game(game_analysis)
            
            # Create response
            response = AnalysisResponse(
                success=True,
                message="Game analyzed successfully",
                analysis=game_analysis.to_dict(),
                annotated_pgn=annotated_pgn
            )
            
            return response
            
        finally:
            engine.close()
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return AnalysisResponse(
            success=False,
            message="Analysis failed",
            error=str(e)
        )


@app.post("/analyze-file", response_model=AnalysisResponse)
async def analyze_game_file(
    file: UploadFile = File(..., description="PGN file to analyze"),
    engine_path: str = Form(..., description="Path to Stockfish executable"),
    shallow_depth: int = Form(default=10, description="Shallow analysis depth"),
    deep_depth: int = Form(default=20, description="Deep analysis depth"),
    multipv: int = Form(default=3, description="Number of top moves to analyze")
):
    """
    Analyze a chess game from uploaded PGN file.
    
    Args:
        file: Uploaded PGN file
        engine_path: Path to Stockfish executable
        shallow_depth: Shallow analysis depth
        deep_depth: Deep analysis depth
        multipv: Number of top moves to analyze
        
    Returns:
        AnalysisResponse with analysis results and annotated PGN
    """
    try:
        # Read file content
        content = await file.read()
        pgn_content = content.decode('utf-8')
        
        # Parse PGN
        pgn_io = io.StringIO(pgn_content)
        game = chess.pgn.read_game(pgn_io)
        
        if game is None:
            raise HTTPException(status_code=400, detail="Invalid PGN format in uploaded file")
        
        # Initialize engine and evaluator
        engine = ChessEngine(engine_path)
        evaluator = MoveEvaluator(engine)
        annotator = PGNAnnotator()
        
        try:
            # Evaluate the game
            move_assessments = evaluator.evaluate_game(
                game, 
                shallow_depth, 
                deep_depth, 
                multipv
            )
            
            # Create game analysis
            game_analysis = GameAnalysis(
                pgn=pgn_content,
                game=game,
                moves=move_assessments,
                total_moves=len(move_assessments)
            )
            
            # Annotate PGN
            annotated_pgn = annotator.annotate_game(game_analysis)
            
            # Create response
            response = AnalysisResponse(
                success=True,
                message="Game analyzed successfully",
                analysis=game_analysis.to_dict(),
                annotated_pgn=annotated_pgn
            )
            
            return response
            
        finally:
            engine.close()
            
    except Exception as e:
        logger.error(f"File analysis failed: {e}")
        return AnalysisResponse(
            success=False,
            message="File analysis failed",
            error=str(e)
        )


@app.post("/analyze-batch")
async def analyze_batch_games(
    request: AnalysisRequest,
    max_games: int = Form(default=10, description="Maximum number of games to analyze")
):
    """
    Analyze multiple games from PGN string (supports multiple games).
    
    Args:
        request: AnalysisRequest containing PGN and parameters
        max_games: Maximum number of games to analyze
        
    Returns:
        Batch analysis results
    """
    try:
        # Parse PGN (may contain multiple games)
        pgn_io = io.StringIO(request.pgn)
        games = []
        
        while True:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break
            games.append(game)
            
            if len(games) >= max_games:
                break
        
        if not games:
            raise HTTPException(status_code=400, detail="No valid games found in PGN")
        
        # Initialize engine and evaluator
        engine = ChessEngine(request.engine_path)
        evaluator = MoveEvaluator(engine)
        annotator = PGNAnnotator()
        
        try:
            game_analyses = []
            
            for i, game in enumerate(games):
                logger.info(f"Analyzing game {i+1}/{len(games)}")
                
                # Evaluate the game
                move_assessments = evaluator.evaluate_game(
                    game, 
                    request.shallow_depth, 
                    request.deep_depth, 
                    request.multipv
                )
                
                # Create game analysis
                game_analysis = GameAnalysis(
                    pgn=str(game),
                    game=game,
                    moves=move_assessments,
                    total_moves=len(move_assessments)
                )
                
                game_analyses.append(game_analysis)
            
            # Create batch result
            batch_result = AnalysisResult(
                games=game_analyses,
                total_games=len(game_analyses),
                total_moves=0  # Will be calculated in __post_init__
            )
            
            # Annotate all games
            annotated_pgns = annotator.batch_annotate_games(game_analyses)
            
            # Create response
            response = {
                "success": True,
                "message": f"Successfully analyzed {len(games)} games",
                "batch_analysis": batch_result.to_dict(),
                "annotated_pgns": annotated_pgns,
                "summary": annotator.create_batch_summary(game_analyses)
            }
            
            return response
            
        finally:
            engine.close()
            
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        return {
            "success": False,
            "message": "Batch analysis failed",
            "error": str(e)
        }


@app.get("/stats")
async def get_stats():
    """Get API usage statistics."""
    return {
        "endpoints": {
            "analyze": "POST - Single game analysis",
            "analyze-file": "POST - File upload analysis", 
            "analyze-batch": "POST - Multiple games analysis"
        },
        "features": [
            "Move quality assessment (Top, Excellent, Good, Mistake, Blunder)",
            "Brilliant move detection",
            "Centipawn analysis",
            "PGN annotation with NAGs and comments",
            "Multi-depth analysis",
            "MultiPV support"
        ],
        "move_labels": {
            "Top": "≤20 cp loss",
            "Excellent": "≤50 cp loss", 
            "Good": "≤120 cp loss",
            "Mistake": "≤300 cp loss",
            "Blunder": ">300 cp loss"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
