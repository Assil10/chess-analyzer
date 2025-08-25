import React, { useState, useEffect, useCallback } from 'react';
import { Chess } from 'chess.js';
import { Chessboard } from 'chessboardjsx';

const ChessBoardViewer = ({ 
  pgn, 
  moves = [], 
  analysis = [], 
  className = "" 
}) => {
  const [chess, setChess] = useState(new Chess());
  const [currentMoveIndex, setCurrentMoveIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [moveHistory, setMoveHistory] = useState([]);
  const [currentPosition, setCurrentPosition] = useState('start');

  // Initialize chess game from PGN or moves
  useEffect(() => {
    const newChess = new Chess();
    
    if (pgn) {
      try {
        newChess.loadPgn(pgn);
        setMoveHistory(newChess.history({ verbose: true }));
        setCurrentPosition(newChess.fen());
      } catch (error) {
        console.error('Invalid PGN:', error);
      }
    } else if (moves.length > 0) {
      try {
        moves.forEach(move => {
          if (typeof move === 'string') {
            newChess.move(move);
          } else if (move.from && move.to) {
            newChess.move(move);
          }
        });
        setMoveHistory(newChess.history({ verbose: true }));
        setCurrentPosition(newChess.fen());
      } catch (error) {
        console.error('Invalid moves:', error);
      }
    }
    
    setChess(newChess);
    setCurrentMoveIndex(-1);
  }, [pgn, moves]);

  // Auto-play effect
  useEffect(() => {
    if (!isPlaying || currentMoveIndex >= moveHistory.length - 1) {
      setIsPlaying(false);
      return;
    }

    const timer = setTimeout(() => {
      goToMove(currentMoveIndex + 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [isPlaying, currentMoveIndex, moveHistory.length]);

  // Navigate to specific move
  const goToMove = useCallback((moveIndex) => {
    const newChess = new Chess();
    
    if (moveIndex === -1) {
      setCurrentPosition(newChess.fen());
      setCurrentMoveIndex(-1);
      setChess(newChess);
      return;
    }

    try {
      for (let i = 0; i <= moveIndex; i++) {
        newChess.move(moveHistory[i]);
      }
      setCurrentPosition(newChess.fen());
      setCurrentMoveIndex(moveIndex);
      setChess(newChess);
    } catch (error) {
      console.error('Error navigating to move:', error);
    }
  }, [moveHistory]);

  // Navigation functions
  const goToStart = () => goToMove(-1);
  const goToEnd = () => goToMove(moveHistory.length - 1);
  const goToPrevious = () => goToMove(Math.max(-1, currentMoveIndex - 1));
  const goToNext = () => goToMove(Math.min(moveHistory.length - 1, currentMoveIndex + 1));

  // Play/Pause toggle
  const togglePlay = () => {
    if (isPlaying) {
      setIsPlaying(false);
    } else {
      if (currentMoveIndex >= moveHistory.length - 1) {
        goToStart();
      }
      setIsPlaying(true);
    }
  };

  // Flip board
  const flipBoard = () => setIsFlipped(!isFlipped);

  // Get current move analysis
  const getCurrentMoveAnalysis = () => {
    if (currentMoveIndex < 0 || currentMoveIndex >= analysis.length) {
      return null;
    }
    return analysis[currentMoveIndex];
  };

  // Format move number and notation
  const formatMoveNumber = (index) => {
    if (index < 0) return '';
    return Math.floor(index / 2) + 1;
  };

  const formatMoveNotation = (index) => {
    if (index < 0 || index >= moveHistory.length) return '';
    return moveHistory[index].san;
  };

  return (
    <div className={`flex gap-6 ${className}`}>
      {/* Left Column - Chess Board */}
      <div className="flex flex-col items-center">
        {/* Chess Board */}
        <div className="mb-4">
          <Chessboard
            position={currentPosition}
            boardOrientation={isFlipped ? 'black' : 'white'}
            width={400}
            height={400}
            boardStyle={{
              borderRadius: '4px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
            squareStyles={{}}
            onPieceDrop={() => false} // Disable piece dragging
          />
        </div>

        {/* Navigation Controls */}
        <div className="flex flex-wrap gap-2 justify-center mb-4">
          <button
            onClick={goToStart}
            disabled={currentMoveIndex === -1}
            className="px-3 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            ⏮️ Start
          </button>
          
          <button
            onClick={goToPrevious}
            disabled={currentMoveIndex === -1}
            className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            ⏪ Previous
          </button>
          
          <button
            onClick={togglePlay}
            className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium"
          >
            {isPlaying ? '⏸️ Pause' : '▶️ Play'}
          </button>
          
          <button
            onClick={goToNext}
            disabled={currentMoveIndex >= moveHistory.length - 1}
            className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            ⏩ Next
          </button>
          
          <button
            onClick={goToEnd}
            disabled={currentMoveIndex >= moveHistory.length - 1}
            className="px-3 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            ⏭️ End
          </button>
        </div>

        {/* Additional Controls */}
        <div className="flex gap-2">
          <button
            onClick={flipBoard}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm font-medium"
          >
            🔄 Flip Board
          </button>
        </div>

        {/* Move Counter */}
        <div className="mt-4 text-center">
          <p className="text-gray-600 text-sm">
            Move {currentMoveIndex + 1} of {moveHistory.length}
          </p>
          {currentMoveIndex >= 0 && (
            <p className="text-gray-800 font-medium">
              {formatMoveNumber(currentMoveIndex)}. {formatMoveNotation(currentMoveIndex)}
            </p>
          )}
        </div>
      </div>

      {/* Right Column - Analysis Panel */}
      <div className="flex-1 min-w-0">
        <div className="bg-white rounded-lg shadow-md p-6 h-full">
          <h3 className="text-xl font-bold text-gray-800 mb-4 border-b pb-2">
            Move Analysis
          </h3>
          
          {currentMoveIndex < 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="text-lg">Click Play or navigate to see move analysis</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Current Move Info */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-semibold text-blue-800 mb-2">
                  Move {formatMoveNumber(currentMoveIndex)}: {formatMoveNotation(currentMoveIndex)}
                </h4>
                <p className="text-blue-600 text-sm">
                  {moveHistory[currentMoveIndex]?.color === 'w' ? 'White' : 'Black'} to move
                </p>
              </div>

              {/* Analysis Data */}
              {getCurrentMoveAnalysis() && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded p-3">
                      <span className="text-gray-600 text-sm font-medium">Quality:</span>
                      <p className="text-gray-800 font-semibold">
                        {getCurrentMoveAnalysis().label || 'N/A'}
                      </p>
                    </div>
                    
                    <div className="bg-gray-50 rounded p-3">
                      <span className="text-gray-600 text-sm font-medium">CP Loss:</span>
                      <p className="text-gray-800 font-semibold">
                        {getCurrentMoveAnalysis().loss_vs_best || 'N/A'}
                      </p>
                    </div>
                  </div>

                  {getCurrentMoveAnalysis().best_move && (
                    <div className="bg-green-50 rounded p-3">
                      <span className="text-green-600 text-sm font-medium">Best Move:</span>
                      <p className="text-green-800 font-semibold">
                        {getCurrentMoveAnalysis().best_move}
                      </p>
                    </div>
                  )}

                  {getCurrentMoveAnalysis().details && (
                    <div className="bg-yellow-50 rounded p-3">
                      <span className="text-yellow-600 text-sm font-medium">Details:</span>
                      <p className="text-yellow-800">
                        {getCurrentMoveAnalysis().details}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Move History */}
              <div className="mt-6">
                <h4 className="font-semibold text-gray-800 mb-3">Move History</h4>
                <div className="max-h-64 overflow-y-auto bg-gray-50 rounded p-3">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {moveHistory.map((move, index) => (
                      <div
                        key={index}
                        className={`p-2 rounded cursor-pointer transition-colors ${
                          index === currentMoveIndex
                            ? 'bg-blue-200 text-blue-800 font-semibold'
                            : 'hover:bg-gray-200'
                        }`}
                        onClick={() => goToMove(index)}
                      >
                        <span className="text-gray-600">
                          {Math.floor(index / 2) + 1}.
                        </span>{' '}
                        {move.san}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChessBoardViewer;
