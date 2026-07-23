export default function FeatureContributions({ contributions, p1Name, p2Name }) {
  if (!contributions || contributions.length === 0) return null

  const maxMagnitude = Math.max(...contributions.map((c) => c.magnitude))

  return (
    <div className="mt-6 border-t border-slate-800 pt-5">
      <p className="text-sm font-semibold text-slate-300">Why this prediction</p>
      <p className="mt-1 text-xs text-slate-500">
        Top factors pushing the prediction toward {p1Name} or {p2Name}, by SHAP contribution.
      </p>

      <div className="mt-4 flex flex-col gap-3">
        {contributions.map((c) => {
          const towardP1 = c.direction === p1Name
          const widthPct = (c.magnitude / maxMagnitude) * 100
          return (
            <div key={c.feature}>
              <div className="flex justify-between text-xs text-slate-400">
                <span>{c.label}</span>
                <span className={towardP1 ? 'text-emerald-400' : 'text-rose-400'}>
                  → {c.direction}
                </span>
              </div>
              <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className={`h-full ${towardP1 ? 'bg-emerald-500' : 'bg-rose-500'}`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
