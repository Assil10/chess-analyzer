import React, { useState, useEffect } from 'react';

// Main App Component
const App = () => {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load the analysis data
  useEffect(() => {
    const loadAnalysisData = async () => {
      try {
        const response = await fetch('./sample_analysis.json');
        if (!response.ok) {
          throw new Error('Failed to load analysis data');
        }
        const data = await response.json();
        setAnalysisData(data);
      } catch (err) {
        console.error('Error loading analysis data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadAnalysisData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chess analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Data</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analysisData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No analysis data available</p>
        </div>
      </div>
    );
  }

  // Extract PGN and moves from the analysis data
  const pgn = analysisData.pgn;
  const moves = analysisData.moves || [];
  
  // Transform the analysis data to match the expected format
  const analysis = moves.map(move => ({
    label: move.label,
    loss_vs_best: move.loss_vs_best,
    best_move: move.best_move,
    details: `${move.is_sacrifice ? '[Sacrifice] ' : ''}${move.is_only_move ? '[Only Move] ' : ''}${move.is_surprise ? '[Surprise] ' : ''}${move.brilliant ? '[Brilliant!] ' : ''}`.trim() || undefined,
    cp_gain: move.cp_gain,
    eval_before: move.eval_before,
    eval_after: move.eval_after,
    material_change: move.material_change
  }));

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <h1 className="text-3xl font-bold text-gray-800">Chess Analysis Viewer</h1>
          <p className="text-gray-600 mt-2">
            Analyzing: {analysisData.white_stats?.name || 'White'} vs {analysisData.black_stats?.name || 'Black'}
          </p>
          
          {/* Game Summary */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-sm text-blue-600 font-medium">Game Quality</div>
              <div className="text-lg font-bold text-blue-800">{analysisData.overall_quality}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-sm text-green-600 font-medium">Overall Accuracy</div>
              <div className="text-lg font-bold text-green-800">{analysisData.game_accuracy}%</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-3">
              <div className="text-sm text-purple-600 font-medium">Total Moves</div>
              <div className="text-lg font-bold text-purple-800">{analysisData.total_moves}</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3">
              <div className="text-sm text-yellow-600 font-medium">Winner</div>
              <div className="text-lg font-bold text-yellow-800">
                {analysisData.white_stats?.accuracy_percentage > analysisData.black_stats?.accuracy_percentage ? 'White' : 'Black'}
              </div>
            </div>
          </div>

          {/* Player Stats */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border rounded-lg p-3">
              <h3 className="font-semibold text-gray-800 mb-2">White ({analysisData.white_stats?.name || 'White'})</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>Accuracy: <span className="font-semibold">{analysisData.white_stats?.accuracy_percentage}%</span></div>
                <div>Blunder Rate: <span className="font-semibold">{analysisData.white_stats?.blunder_rate}%</span></div>
                <div>Best Moves: <span className="font-semibold">{analysisData.white_stats?.best_moves}</span></div>
                <div>Great Moves: <span className="font-semibold">{analysisData.white_stats?.great_moves}</span></div>
              </div>
            </div>
            <div className="bg-white border rounded-lg p-3">
              <h3 className="font-semibold text-gray-800 mb-2">Black ({analysisData.black_stats?.name || 'Black'})</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>Accuracy: <span className="font-semibold">{analysisData.black_stats?.accuracy_percentage}%</span></div>
                <div>Blunder Rate: <span className="font-semibold">{analysisData.black_stats?.blunder_rate}%</span></div>
                <div>Best Moves: <span className="font-semibold">{analysisData.black_stats?.best_moves}</span></div>
                <div>Great Moves: <span className="font-semibold">{analysisData.black_stats?.great_moves}</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chess Board Viewer */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <ChessBoardViewer
            pgn={pgn}
            analysis={analysis}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
};

// Render the app
ReactDOM.render(<App />, document.getElementById('root'));
