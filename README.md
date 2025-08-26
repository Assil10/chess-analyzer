# Chess Analysis AI (Top & Brilliant Move Detector).

A comprehensive chess analysis system that combines Python backend analysis with a React frontend viewer for interactive chess game analysis.

## 🎯 Project Overview

This project consists of two main components:

1. **Python Backend**: Advanced chess analysis using Stockfish engine with move classification and accuracy scoring
2. **React Frontend**: Interactive chess board viewer with move navigation and analysis display

## 🚀 Features

### Python Backend Analysis
- **Stockfish Integration**: Deep analysis using Stockfish chess engine
- **Move Classification**: Labels moves as Brilliant, Great, Best, Excellent, Good, Inaccuracy, Mistake, or Blunder
- **Accuracy Calculation**: Weighted accuracy scoring similar to Chess.com
- **PGN Support**: Analyze games from PGN format
- **JSON Output**: Structured analysis data for frontend consumption

### React Frontend Viewer
- **Interactive Chess Board**: Visual representation of game positions
- **Move Navigation**: Previous, Next, Start, End controls
- **Auto-play**: Automatic move progression at 1 move per second
- **Analysis Panel**: Real-time display of move quality, CP loss, and best moves
- **Move History**: Clickable move list with current position highlighting
- **Responsive Design**: Modern UI built with Tailwind CSS

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+ (for React development)
- Stockfish chess engine

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Download Stockfish
# Visit: https://stockfishchess.org/download/
# Place stockfish executable in stockfish/ directory
```

### Frontend Setup
```bash
# Install Node.js dependencies (optional - CDN version works)
npm install

# Or use the CDN version (already configured in index.html)
# No build step required - runs directly in browser
```

## 📖 Usage

### Running Chess Analysis
```bash
# Analyze a PGN file
python scripts/analyze.py analyze -p examples/sample_game.pgn -e stockfish/stockfish-windows-x86-64-avx2.exe -j sample_analysis.json

# View help
python scripts/analyze.py --help
```

### Running the React Viewer
```bash
# Start the local server
python serve.py

# Open browser to: http://localhost:8000
```

## 🎮 React Component: ChessBoardViewer

The main React component that provides an interactive chess analysis interface.

### Props
- `pgn`: PGN string of the chess game
- `moves`: Array of move objects (alternative to PGN)
- `analysis`: Array of analysis data for each move
- `className`: Additional CSS classes

### Features
- **Chess Board Display**: Visual board representation
- **Move Controls**: Navigation buttons for game progression
- **Analysis Display**: Real-time move quality and statistics
- **Move History**: Interactive move list with click navigation
- **Auto-play**: Automatic move progression
- **Board Flipping**: Switch between white/black perspective

### Example Usage
```jsx
<ChessBoardViewer
  pgn={gamePgn}
  analysis={moveAnalysis}
  className="w-full"
/>
```

## 📁 Project Structure

```
chess-analyzer/
├── scripts/
│   ├── analyze.py          # Main analysis script
│   └── chess_analyzer.py   # Core analysis logic
├── examples/
│   └── sample_game.pgn     # Sample chess game
├── stockfish/              # Stockfish engine directory
├── index.html              # Main React application
├── serve.py                # Local development server
├── sample_analysis.json    # Analysis output
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies
└── README.md              # This file
```

## 🔧 Technical Details

### Backend Technologies
- **Python**: Core analysis logic
- **python-chess**: Chess game handling
- **Stockfish**: Chess engine for analysis
- **JSON**: Data output format

### Frontend Technologies
- **React 18**: Modern React with hooks
- **Tailwind CSS**: Utility-first CSS framework
- **Babel**: In-browser JSX transformation
- **CDN Libraries**: React, chess.js, chessboardjsx loaded via CDN

### Data Flow
1. Python backend analyzes PGN → generates JSON
2. React frontend loads JSON → displays analysis
3. User interacts with viewer → navigates through moves
4. Real-time analysis display → shows move quality and details

## 🎨 UI Components

### Game Summary Dashboard
- Overall game quality and accuracy
- Player statistics comparison
- Move count and winner information

### Chess Board Viewer
- Interactive chess board (placeholder)
- Navigation controls
- Move counter and notation

### Analysis Panel
- Current move information
- Quality classification
- CP loss and best move data
- Special move indicators (Sacrifice, Only Move, etc.)

## 🚀 Development

### Local Development
```bash
# Start Python server
python serve.py

# Access at http://localhost:8000
# No build step required - edit index.html directly
```

### Adding Features
- **New Analysis Metrics**: Modify `scripts/chess_analyzer.py`
- **UI Enhancements**: Edit React components in `index.html`
- **Styling Changes**: Update Tailwind classes

## 📊 Sample Output

The system generates comprehensive analysis including:
- Move-by-move quality assessment
- Centipawn loss calculations
- Best move recommendations
- Player accuracy percentages
- Game quality classification

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Stockfish chess engine team
- python-chess library contributors
- React and Tailwind CSS communities

---

**Note**: This project combines the power of Python chess analysis with modern React web technologies to create an interactive chess analysis experience.
