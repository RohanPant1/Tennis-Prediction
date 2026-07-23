import usePlayers from './api/usePlayers'
import usePredictor from './api/usePredictor'
import Header from './components/Header'
import PredictorCard from './components/PredictorCard'
import LoadingState from './components/LoadingState'
import ErrorState from './components/ErrorState'
import ResultDisplay from './components/ResultDisplay'
import AboutModel from './components/AboutModel'
import Footer from './components/Footer'

function App() {
  const { players } = usePlayers()
  const predictor = usePredictor()

  return (
    <div className="min-h-screen bg-slate-950">
      <Header />

      <main className="mx-auto max-w-2xl px-4 pb-4">
        <PredictorCard predictor={predictor} players={players} />

        {predictor.loading && <LoadingState isSlow={predictor.isSlow} />}
        {predictor.error && !predictor.loading && <ErrorState message={predictor.error} />}
        {predictor.result && !predictor.loading && !predictor.error && (
          <ResultDisplay
            result={predictor.result}
            p1Name={predictor.p1}
            p2Name={predictor.p2}
            surface={predictor.surface}
          />
        )}
      </main>

      <AboutModel />
      <Footer />
    </div>
  )
}

export default App
