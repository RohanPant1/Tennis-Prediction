import { useEffect, useState } from 'react'
import client from './client'

export default function usePlayers() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    client.get('/players')
      .then((res) => {
        if (!cancelled) setPlayers(res.data.players)
      })
      .catch((err) => {
        if (!cancelled) setError(err)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [])

  return { players, loading, error }
}
