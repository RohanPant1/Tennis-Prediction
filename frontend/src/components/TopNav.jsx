const TABS = [
  { key: 'predict', label: 'Predict' },
  { key: 'about', label: 'About the Model' },
]

export default function TopNav({ view, setView }) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🎾</span>
          <span className="font-semibold text-slate-100">Tennis Match Predictor</span>
        </div>

        <div className="inline-flex rounded-lg border border-slate-700 bg-slate-900 p-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setView(tab.key)}
              className={`rounded-md px-3.5 py-1.5 text-sm font-medium transition ${
                view === tab.key
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  )
}
