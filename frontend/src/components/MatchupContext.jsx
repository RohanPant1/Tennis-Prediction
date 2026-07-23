function FormStrip({ results }) {
  return (
    <div className="mt-1 flex gap-1">
      {results.map((r, i) => (
        <span
          key={i}
          className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
            r === 'W' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
          }`}
        >
          {r}
        </span>
      ))}
    </div>
  )
}

function PlayerCard({ name, playerCtx, surface }) {
  return (
    <div className="flex-1 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
      <p className="truncate text-sm font-semibold text-slate-200">{name}</p>

      <div className="mt-3">
        <p className="text-xs uppercase tracking-wide text-slate-500">{surface} Elo</p>
        <p className="text-xl font-bold text-slate-100">{Math.round(playerCtx.surface_elo)}</p>
        {playerCtx.surface_elo_is_fallback && (
          <p className="mt-0.5 text-xs text-slate-500">
            No {surface.toLowerCase()}-court history yet — showing overall rating
          </p>
        )}
      </div>

      <div className="mt-3">
        <p className="text-xs uppercase tracking-wide text-slate-500">
          Last {playerCtx.recent_form.results.length}
        </p>
        <p className="text-sm text-slate-300">
          {playerCtx.recent_form.wins}W – {playerCtx.recent_form.losses}L
        </p>
        {playerCtx.recent_form.results.length > 0 && (
          <FormStrip results={playerCtx.recent_form.results} />
        )}
      </div>
    </div>
  )
}

export default function MatchupContext({ context, p1Name, p2Name, surface }) {
  if (!context) return null

  return (
    <div className="mt-6 border-t border-slate-800 pt-5">
      <p className="text-sm font-semibold text-slate-300">Matchup context</p>

      <div className="mt-3 flex flex-col gap-3 sm:flex-row">
        <PlayerCard name={p1Name} playerCtx={context.p1} surface={surface} />
        <PlayerCard name={p2Name} playerCtx={context.p2} surface={surface} />
      </div>

      <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-center">
        <p className="text-xs uppercase tracking-wide text-slate-500">Head-to-head</p>
        {context.h2h.matches === 0 ? (
          <p className="mt-1 text-sm text-slate-400">No previous meetings on record</p>
        ) : (
          <p className="mt-1 text-sm text-slate-200">
            {p1Name} <span className="font-bold">{context.h2h.p1_wins}</span> –{' '}
            <span className="font-bold">{context.h2h.p2_wins}</span> {p2Name}
          </p>
        )}
      </div>
    </div>
  )
}
