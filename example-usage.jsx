import React from 'react';
import ChessBoardViewer from './ChessBoardViewer';

// Example usage of ChessBoardViewer component
const ExampleUsage = () => {
  // Sample PGN string
  const samplePGN = `1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7`;

  // Sample analysis data (matching the structure from your chess analyzer)
  const sampleAnalysis = [
    {
      label: "MoveLabel.BEST_MOVE",
      loss_vs_best: 0,
      best_move: "e4",
      details: "Best opening move"
    },
    {
      label: "MoveLabel.EXCELLENT",
      loss_vs_best: 15,
      best_move: "e5",
      details: "Classical response"
    },
    {
      label: "MoveLabel.GOOD",
      loss_vs_best: 25,
      best_move: "Nf3",
      details: "Develops knight, controls center"
    },
    {
      label: "MoveLabel.GOOD",
      loss_vs_best: 30,
      best_move: "Nc6",
      details: "Natural development"
    },
    {
      label: "MoveLabel.BEST_MOVE",
      loss_vs_best: 0,
      best_move: "Bb5",
      details: "Ruy Lopez opening"
    },
    {
      label: "MoveLabel.INACCURACY",
      loss_vs_best: 45,
      best_move: "a6",
      details: "Prevents Bxc6"
    },
    {
      label: "MoveLabel.GOOD",
      loss_vs_best: 35,
      best_move: "Ba4",
      details: "Retreats bishop"
    },
    {
      label: "MoveLabel.EXCELLENT",
      loss_vs_best: 12,
      best_move: "Nf6",
      details: "Develops knight, attacks e4"
    },
    {
      label: "MoveLabel.BEST_MOVE",
      loss_vs_best: 0,
      best_move: "O-O",
      details: "Castles kingside"
    },
    {
      label: "MoveLabel.GOOD",
      loss_vs_best: 28,
      best_move: "Re1",
      details: "Prepares d4"
    }
  ];

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">
          Chess Board Viewer Example
        </h1>
        
        <div className="bg-white rounded-lg shadow-lg p-6">
          <ChessBoardViewer
            pgn={samplePGN}
            analysis={sampleAnalysis}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
};

export default ExampleUsage;
