import { useRef, useState } from 'react'
import client from './client'

const COLD_START_DELAY_MS = 4000

function todayISODate() {
  return new Date().toISOString().slice(0, 10)
}

export default function usePredictor() {
  const [p1, setP1] = useState('Carlos Alcaraz')
  const [p2, setP2] = useState('Jannik Sinner')
  const [dateMode, setDateMode] = useState('present') // 'present' | 'past'
  const [pastDate, setPastDate] = useState(todayISODate())
  const [surface, setSurface] = useState('Hard')
  const [tourneyLevel, setTourneyLevel] = useState('A')
  const [roundIdx, setRoundIdx] = useState(7)
  const [drawSize, setDrawSize] = useState(32)
  const [bestOf, setBestOf] = useState(3)

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [isSlow, setIsSlow] = useState(false)
  const [error, setError] = useState(null)

  const slowTimer = useRef(null)

  const swapPlayers = () => {
    setP1(p2)
    setP2(p1)
  }

  const sameSelected = p1.trim() !== '' && p2.trim() !== '' &&
    p1.trim().toLowerCase() === p2.trim().toLowerCase()

  const validationError = (() => {
    if (p1.trim() === '' || p2.trim() === '') return 'Pick both Player 1 and Player 2.'
    if (sameSelected) return 'Player 1 and Player 2 must be different.'
    return null
  })()

  const canSubmit = validationError === null && !loading

  const predict = async () => {
    if (!canSubmit) return

    setLoading(true)
    setIsSlow(false)
    setError(null)
    setResult(null)

    slowTimer.current = setTimeout(() => setIsSlow(true), COLD_START_DELAY_MS)

    try {
      const response = await client.post('/predict', {
        p1,
        p2,
        target_date: dateMode === 'present' ? todayISODate() : pastDate,
        surface,
        draw_size: parseInt(drawSize, 10),
        best_of: parseInt(bestOf, 10),
        tourney_level: tourneyLevel,
        round_idx: parseInt(roundIdx, 10),
      })
      setResult(response.data)
    } catch (err) {
      const message = err.response?.data?.detail || 'Backend not reachable. Is it running?'
      setError(message)
    } finally {
      clearTimeout(slowTimer.current)
      setLoading(false)
      setIsSlow(false)
    }
  }

  return {
    p1, setP1, p2, setP2, swapPlayers, sameSelected,
    dateMode, setDateMode, pastDate, setPastDate,
    surface, setSurface, tourneyLevel, setTourneyLevel,
    roundIdx, setRoundIdx, drawSize, setDrawSize, bestOf, setBestOf,
    result, loading, isSlow, error, validationError, canSubmit,
    predict,
  }
}
