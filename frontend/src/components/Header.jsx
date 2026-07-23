export default function Header() {
  return (
    <header className="mx-auto max-w-2xl px-4 pt-10 pb-6 text-center">
      <h1 className="text-3xl font-bold text-slate-100 sm:text-4xl">🎾 Tennis Match Predictor</h1>
      <p className="mt-2 text-slate-400">
        Predicts ATP match outcomes from a custom Elo system and rolling form stats.
      </p>
      <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-emerald-800
                      bg-emerald-950/50 px-4 py-1.5 text-sm font-medium text-emerald-400">
        0.727 ROC-AUC on unseen, chronologically later matches
      </div>
    </header>
  )
}
