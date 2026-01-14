import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'



function App() {
  // State variables for all prediction parameters
  const [p1, setP1] = useState('Jannik Sinner');
  const [p2, setP2] = useState('Carlos Alcaraz');
  const [targetDate, setTargetDate] = useState('2026-01-14');
  const [surface, setSurface] = useState('Hard');
  const [drawSize, setDrawSize] = useState(128);
  const [bestOf, setBestOf] = useState(5);
  const [tourneyLevel, setTourneyLevel] = useState('G');
  const [roundIdx, setRoundIdx] = useState(6);

  const handlePredict = async () => {
    const payload = {
      p1,
      p2,
      target_date: targetDate,
      surface,
      draw_size: parseInt(drawSize),
      best_of: parseInt(bestOf),
      tourney_level: tourneyLevel,
      round_idx: parseInt(roundIdx),
    };

    console.log("Sending prediction request:", payload);
    // In the next step, you will use axios to post this to your FastAPI backend
  };

  return (
    <div className="App">
      <h1>🎾 Tennis Match Predictor</h1>
      
      <div className="card form-container">
        <div className="input-group">
          <label>Player 1:</label>
          <input value={p1} onChange={(e) => setP1(e.target.value)} />
        </div>

        <div className="input-group">
          <label>Player 2:</label>
          <input value={p2} onChange={(e) => setP2(e.target.value)} />
        </div>

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
            <option value="D">Davis Cup (D)</option>
            <option value="F">Tour Finals (F)</option>
          </select>
        </div>

        <div className="input-group">
          <label>Round (0-7):</label>
          <input type="number" min="0" max="7" value={roundIdx} onChange={(e) => setRoundIdx(e.target.value)} />
        </div>

        <div className="input-group">
          <label>Best Of:</label>
          <select value={bestOf} onChange={(e) => setBestOf(e.target.value)}>
            <option value="3">3 Sets</option>
            <option value="5">5 Sets</option>
          </select>
        </div>

        <div className="input-group">
          <label>Draw Size:</label>
          <input type="number" value={drawSize} onChange={(e) => setDrawSize(e.target.value)} />
        </div>

        <button onClick={handlePredict} className="predict-btn">Predict Winner</button>
      </div>
    </div>
  );
}

export default App;