import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import axios from 'axios'

function App() {
  // Initial values set for Alcaraz vs Sinner at a 2026 Grand Slam
  const [p1, setP1] = useState('Carlos Alcaraz');
  const [p2, setP2] = useState('Jannik Sinner');
  const [targetDate, setTargetDate] = useState('2026-01-14');
  const [surface, setSurface] = useState('Hard');
  const [drawSize, setDrawSize] = useState(128);
  const [bestOf, setBestOf] = useState(5);
  const [tourneyLevel, setTourneyLevel] = useState('G');
  const [roundIdx, setRoundIdx] = useState(0);

  // State for handling the API response and UI status
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePredict = async () => {
    setLoading(true);
    setResult(null);
    try {
      const response = await axios.post('http://localhost:8000/predict', {
        p1, p2, target_date: targetDate, surface,
        draw_size: parseInt(drawSize),
        best_of: parseInt(bestOf),
        tourney_level: tourneyLevel,
        round_idx: parseInt(roundIdx)
      });
      setResult(response.data);
    } catch (error) {
      alert("Error: " + (error.response?.data?.error || "Backend not reachable"));
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="App">
      <h1>🎾 Tennis Match Predictor</h1>
      
      <div className="card form-container">
        {/* Player Selection */}
        <div className="input-group">
          <label>Player 1:</label>
          <input value={p1} onChange={(e) => setP1(e.target.value)} />
        </div>
        <div className="input-group">
          <label>Player 2:</label>
          <input value={p2} onChange={(e) => setP2(e.target.value)} />
        </div>

        {/* Match Context */}
        <div className="input-group">
          <label>Date:</label>
          <input type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} />
        </div>

        <div className="input-group">
          <label>Surface:</label>
          <select value={surface} onChange={(e) => setSurface(e.target.value)}>
            <option value="Hard">Hard</option>
            <option value="Clay">Clay</option>
            <option value="Grass">Grass</option>
          </select>
        </div>

        <div className="input-group">
          <label>Tournament Level:</label>
          <select value={tourneyLevel} onChange={(e) => setTourneyLevel(e.target.value)}>
            <option value="G">Grand Slam (G)</option>
            <option value="M">Masters 1000 (M)</option>
            <option value="A">ATP Tour (A)</option>
          </select>
        </div>

        <div className="input-group">
          <label>Round (0-7):</label>
          <input type="number" min="0" max="7" value={roundIdx} onChange={(e) => setRoundIdx(e.target.value)} />
        </div>

        <button 
          onClick={handlePredict} 
          disabled={loading} 
          className="predict-btn"
        >
          {loading ? "Calculating..." : "Predict Winner"}
        </button>
      </div>

      {/* Results Display */}
      {result && !result.error && (
        <div className="result-card">
          <h2>Prediction</h2>
          <p>Predicted Winner: <strong>{result.winner}</strong></p>
          <p>Probability of {p1}: <strong>{result.p1_prob*100}%</strong></p>
          <p>Probability of {p2}: <strong>{result.p2_prob*100}%</strong></p>
        </div>
      )}

      {result?.error && (
        <div className="error-card">
          <p>Error: {result.error}</p>
        </div>
      )}
    </div>
  );
}

export default App;