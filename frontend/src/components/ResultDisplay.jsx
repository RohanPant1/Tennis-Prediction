export default function ResultDisplay({ result, p1Name, p2Name }) {
  const p1Pct = result.p1_prob * 100
  const p2Pct = result.p2_prob * 100

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
      <p className="text-sm uppercase tracking-wide text-slate-400">Predicted winner</p>
      <p className="mt-1 text-2xl font-bold text-emerald-400">{result.winner}</p>

      <div className="mt-5">
        <div className="flex justify-between text-sm font-medium text-slate-300">
          <span>{p1Name} · {p1Pct.toFixed(1)}%</span>
          <span>{p2Name} · {p2Pct.toFixed(1)}%</span>
        </div>
        <div className="mt-2 flex h-4 w-full overflow-hidden rounded-full bg-slate-800">
          <div
            className="h-full bg-emerald-500 transition-all"
            style={{ width: `${p1Pct}%` }}
          />
          <div
            className="h-full bg-rose-500 transition-all"
            style={{ width: `${p2Pct}%` }}
          />
        </div>
      </div>

      <p className="mt-5 text-sm text-slate-500">
        Even bookmakers reach about 70% accuracy on single matches. Treat this as an informed
        estimate, not a certainty. The model scores 0.727 ROC-AUC on unseen, chronologically
        later matches, and its underlying data runs through Roland Garros 2026.
      </p>
    </div>
  )
}
