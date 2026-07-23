const STATS = [
  { label: 'ROC-AUC', value: '0.727', hint: 'on unseen, chronologically later matches' },
  { label: 'Algorithm', value: 'CatBoost', hint: 'gradient-boosted decision trees' },
  { label: 'Training data', value: '47,451', hint: 'ATP matches through Roland Garros 2026' },
]

const TECH_STACK = ['React', 'Vite', 'Tailwind CSS', 'FastAPI', 'CatBoost', 'scikit-learn']

const FEATURE_GROUPS = [
  { label: 'Ratings & attributes', count: 6, items: 'match Elo, serve Elo, return Elo, ATP ranking points, age, height' },
  { label: 'Recent form, last 52 weeks', count: 7, items: 'ace rate, double-fault rate, 1st-serve-in %, 1st-serve points won %, 2nd-serve points won %, break points saved %, break points converted %' },
  { label: 'History', count: 4, items: 'career matches played, matches played on this surface, head-to-head win difference, head-to-head matches played' },
  { label: 'Surface interactions', count: 2, items: 'return rating on clay, serve rating on grass' },
  { label: 'Match context', count: 2, items: 'draw size, best-of format' },
  { label: 'Surface, one-hot', count: 3, items: 'clay, grass, hard' },
  { label: 'Tournament level, one-hot', count: 7, items: 'tour-level, challenger, Davis Cup, Tour Finals, Grand Slam, Masters 1000, Olympics/other' },
  { label: 'Round, one-hot', count: 8, items: 'early/unknown through the final' },
]

export default function AboutModel() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-100 sm:text-3xl">About the model</h1>
        <p className="mt-2 text-slate-400">
          What the prediction is based on, and how it was tested.
        </p>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {STATS.map((s) => (
          <div
            key={s.label}
            className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-center shadow-xl"
          >
            <p className="text-sm font-medium text-slate-400">{s.label}</p>
            <p className="mt-1 text-3xl font-bold text-emerald-400">{s.value}</p>
            <p className="mt-1 text-xs text-slate-500">{s.hint}</p>
          </div>
        ))}
      </div>

      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-200">What goes into a prediction</h2>
        <div className="mt-3 flex flex-col gap-3 text-sm leading-relaxed text-slate-400">
          <p>
            The model runs on 39 features. A lot of the actual work was figuring out which ones
            mattered and which were just noise.
          </p>

          <ul className="flex flex-col gap-1.5">
            {FEATURE_GROUPS.map((g) => (
              <li key={g.label}>
                <span className="font-semibold text-slate-300">{g.label} ({g.count})</span>
                {' - '}{g.items}
              </li>
            ))}
          </ul>

          <p>
            The core is Elo with three ratings per player: overall match results, serve, and
            return. Splitting serve and return apart gives the model a real read on how someone
            plays, not just how often they win. A serve-heavy player might dominate on a fast
            hard court but struggle against a strong returner on clay, and a single combined
            rating would never catch that.
          </p>
          <p>
            Each rating also comes in a global and a surface-specific version. Early on, if a
            player's barely touched clay, there's not enough signal to trust a clay-specific
            number, so the model leans on their global rating instead. Ratings decay too: if a
            player goes quiet for a few months, their rating drifts back toward a neutral 1500,
            roughly halving the gap every 365 days of inactivity, so a long injury layoff doesn't
            leave them looking artificially strong or weak.
          </p>
          <p>
            Head-to-head was also interesting, since rankings and pure stats can mislead. Zverev
            is the better player on paper, but Fritz has had his number for years, so the
            head-to-head is important for cases like these.
          </p>
          <p>
            I also tried adding fatigue features early on, things like days since a player's last
            match or how many matches they'd played in the past couple weeks. I ended up pulling
            them out as the feature set was already getting big, and fatigue added complexity
            without a clear payoff.
          </p>
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-200">How I tested it</h2>
        <div className="mt-3 flex flex-col gap-3 text-sm leading-relaxed text-slate-400">
          <p>
            I evaluated this with time-series cross-validation instead of a random train/test
            split, on purpose. A random split would let the model peek at matches that happened
            after the ones it's being tested on, which leaks future information (rankings, form,
            head-to-head results) into training.
          </p>
          <p>
            With a chronological split, the model only ever trains on matches from before
            whatever it's being scored on. The 0.727 ROC-AUC above comes from matches that
            happened strictly after anything it trained on, which is a much closer stand-in for
            predicting a match that hasn't happened yet. One caveat: the data itself stops at
            Roland Garros 2026 as of now, so anything predicted past that date is based on each
            player's last known form, not what they're doing right now.
          </p>
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-200">Reading "why this prediction"</h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-400">
          Each result on the Predict page comes with a short breakdown of what drove it. Bars
          pointing left, in green, favor Player 1. Bars pointing right, in red, favor Player 2.
          The longer the bar, the more that factor mattered for this matchup. This comes from
          SHAP (SHapley Additive exPlanations), a common method for explaining what drove a
          single prediction.
        </p>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-200">Built with</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {TECH_STACK.map((t) => (
            <span
              key={t}
              className="rounded-full border border-slate-700 bg-slate-950/50 px-3 py-1 text-sm text-slate-300"
            >
              {t}
            </span>
          ))}
        </div>
      </section>
    </main>
  )
}
