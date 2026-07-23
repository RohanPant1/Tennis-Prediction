import { useEffect, useMemo, useRef, useState } from 'react'

function rankMatches(players, query, exclude) {
  const q = query.trim().toLowerCase()
  if (q === '') return []

  const prefix = []
  const substring = []

  for (const name of players) {
    if (name === exclude) continue
    const lower = name.toLowerCase()
    if (lower.startsWith(q)) prefix.push(name)
    else if (lower.includes(q)) substring.push(name)
  }

  return [...prefix, ...substring].slice(0, 8)
}

export default function PlayerAutocomplete({ label, players, value, onChange, otherValue }) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const containerRef = useRef(null)

  const matches = useMemo(
    () => rankMatches(players, value, otherValue),
    [players, value, otherValue]
  )

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectPlayer = (name) => {
    onChange(name)
    setIsOpen(false)
    setActiveIndex(-1)
  }

  const handleKeyDown = (e) => {
    if (!isOpen || matches.length === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => (i + 1) % matches.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => (i - 1 + matches.length) % matches.length)
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0) {
        e.preventDefault()
        selectPlayer(matches[activeIndex])
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  const inputId = `player-autocomplete-${label.replace(/\s+/g, '-').toLowerCase()}`

  return (
    <div ref={containerRef} className="relative flex flex-col gap-1">
      <label htmlFor={inputId} className="text-sm font-medium text-slate-300">{label}</label>
      <input
        id={inputId}
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value)
          setIsOpen(true)
          setActiveIndex(-1)
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={handleKeyDown}
        className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100
                   placeholder-slate-500 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
        placeholder="Start typing a player name…"
        autoComplete="off"
      />
      {isOpen && matches.length > 0 && (
        <ul className="absolute top-full left-0 z-10 mt-1 max-h-56 w-full overflow-y-auto rounded-lg
                       border border-slate-700 bg-slate-900 shadow-lg">
          {matches.map((name, i) => (
            <li key={name}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => selectPlayer(name)}
                className={`w-full px-3 py-2 text-left text-sm ${
                  i === activeIndex ? 'bg-emerald-600 text-white' : 'text-slate-200 hover:bg-slate-800'
                }`}
              >
                {name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
