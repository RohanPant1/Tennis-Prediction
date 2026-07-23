export default function FeatureContributions({ contributions, p1Name, p2Name }) {
  if (!contributions || contributions.length === 0) return null

  const maxMagnitude = Math.max(...contributions.map((c) => c.magnitude))

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
      <p className="text-sm font-semibold text-slate-300">Why this prediction</p>
      <p className="mt-1 text-xs text-slate-500">
        Top factors behind this prediction, ranked by SHAP contribution.
      </p>

      <div className="mt-4 flex flex-col gap-3">
        {contributions.map((c) => {
          // direction is real signed SHAP output from the backend (predict_stats.py
          // get_feature_contributions) — the bar geometry below shows it directly.
          const towardP1 = c.direction === p1Name
          const widthPct = (c.magnitude / maxMagnitude) * 100
          return (
            <div key={c.feature}>
              <p className="text-xs text-slate-400">{c.label}</p>
              <div className="mt-1 flex h-2 w-full items-center">
                <div className="flex h-full flex-1 justify-end overflow-hidden rounded-l-full bg-slate-800">
                  {towardP1 && (
                    <div
                      className="h-full rounded-l-full bg-emerald-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  )}
                </div>
                <div className="h-3 w-px shrink-0 bg-slate-600" />
                <div className="flex h-full flex-1 justify-start overflow-hidden rounded-r-full bg-slate-800">
                  {!towardP1 && (
                    <div
                      className="h-full rounded-r-full bg-rose-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-slate-800 pt-3 text-xs">
        <span className="text-emerald-400">← favors {p1Name}</span>
        <span className="text-rose-400">favors {p2Name} →</span>
      </div>
    </div>
  )
}
