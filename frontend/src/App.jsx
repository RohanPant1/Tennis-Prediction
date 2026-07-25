import { useState } from 'react'
import usePlayers from './api/usePlayers'
import usePredictor from './api/usePredictor'
import TopNav from './components/TopNav'
import PredictorCard from './components/PredictorCard'
import LoadingState from './components/LoadingState'
import ErrorState from './components/ErrorState'
import ResultDisplay from './components/ResultDisplay'
import MatchupContext from './components/MatchupContext'
import FeatureContributions from './components/FeatureContributions'
import AboutModel from './components/AboutModel'
import Footer from './components/Footer'

function App() {
  const [view, setView] = useState('predict')
  const { players } = usePlayers()
  const predictor = usePredictor()

  const showResult = predictor.result && !predictor.loading && !predictor.error

  return (
    <div className="min-h-screen bg-slate-950">
      <TopNav view={view} setView={setView} />

      <div className="border-b border-slate-800 bg-amber-950/20 px-4 py-2 text-center text-xs text-amber-400">
        Data is sourced from January 2017 till Roland Garros 2026. Matches after that date aren't reflected in ratings or predictions. H2H may not be fully accurate
      </div>

      {view === 'predict' ? (
        <main className="mx-auto max-w-6xl px-4 py-8">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <PredictorCard predictor={predictor} players={players} />

            <div className="flex flex-col gap-6">
              {predictor.loading && <LoadingState isSlow={predictor.isSlow} />}
              {predictor.error && !predictor.loading && <ErrorState message={predictor.error} />}
              {showResult && (
                <ResultDisplay
                  result={predictor.result}
                  p1Name={predictor.p1}
                  p2Name={predictor.p2}
                />
              )}
            </div>
          </div>

          {showResult && (
            <div className="mt-6 flex flex-col gap-6">
              <MatchupContext
                context={predictor.result.context}
                p1Name={predictor.p1}
                p2Name={predictor.p2}
                surface={predictor.surface}
              />
              <FeatureContributions
                contributions={predictor.result.contributions}
                p1Name={predictor.p1}
                p2Name={predictor.p2}
              />
            </div>
          )}
        </main>
      ) : (
        <AboutModel />
      )}

      <Footer />
    </div>
  )
}

export default App
