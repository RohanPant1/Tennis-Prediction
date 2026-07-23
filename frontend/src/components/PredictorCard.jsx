import { useState } from 'react'
import PlayerAutocomplete from './PlayerAutocomplete'

const ROUND_LABELS = {
  7: 'Final', 6: 'Semifinal', 5: 'Quarterfinal', 4: 'Round of 16',
  3: 'Round of 32', 2: 'Round of 64', 1: 'Round of 128', 0: 'Other / Unknown',
}

const TOURNEY_LEVELS = {
  G: 'Grand Slam', M: 'Masters 1000', A: 'Tour-level (250/500)',
  C: 'Challenger', D: 'Davis Cup', F: 'Tour Finals', O: 'Olympics / Other',
}

export default function PredictorCard({ predictor, players }) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <div className="flex-1">
          <PlayerAutocomplete
            label="Player 1"
            players={players}
            value={predictor.p1}
            onChange={predictor.setP1}
            otherValue={predictor.p2}
          />
        </div>

        <button
          type="button"
          onClick={predictor.swapPlayers}
          title="Swap players"
          className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center self-center rounded-full
                     border border-slate-700 bg-slate-800 text-slate-300 transition hover:bg-slate-700
                     sm:self-end"
        >
          ⇄
        </button>

        <div className="flex-1">
          <PlayerAutocomplete
            label="Player 2"
            players={players}
            value={predictor.p2}
            onChange={predictor.setP2}
            otherValue={predictor.p1}
          />
        </div>
      </div>

      {predictor.validationError && (
        <p className="mt-3 text-sm text-amber-400">{predictor.validationError}</p>
      )}

      {/* Present / Past toggle — always visible, the one exception to "advanced options" */}
      <div className="mt-5">
        <span className="text-sm font-medium text-slate-300">Match date</span>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-lg border border-slate-700 bg-slate-900 p-1">
            {['present', 'past'].map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => predictor.setDateMode(mode)}
                className={`rounded-md px-3 py-1.5 text-sm font-medium capitalize transition ${
                  predictor.dateMode === mode
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
          {predictor.dateMode === 'past' && (
            <input
              type="date"
              value={predictor.pastDate}
              onChange={(e) => predictor.setPastDate(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-slate-100
                         outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
          )}
        </div>
      </div>

      {/* Advanced options — collapsed by default */}
      <div className="mt-5 border-t border-slate-800 pt-4">
        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          className="text-sm font-medium text-emerald-400 hover:text-emerald-300"
        >
          {showAdvanced ? '– Hide advanced options' : '+ Advanced options'}
        </button>

        {showAdvanced && (
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col gap-1">
              <label htmlFor="adv-surface" className="text-sm font-medium text-slate-300">Surface</label>
              <select
                id="adv-surface"
                value={predictor.surface}
                onChange={(e) => predictor.setSurface(e.target.value)}
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100
                           outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              >
                <option value="Hard">Hard</option>
                <option value="Clay">Clay</option>
                <option value="Grass">Grass</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="adv-tourney-level" className="text-sm font-medium text-slate-300">Tournament level</label>
              <select
                id="adv-tourney-level"
                value={predictor.tourneyLevel}
                onChange={(e) => predictor.setTourneyLevel(e.target.value)}
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100
                           outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              >
                {Object.entries(TOURNEY_LEVELS).map(([code, label]) => (
                  <option key={code} value={code}>{label}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="adv-round" className="text-sm font-medium text-slate-300">Round</label>
              <select
                id="adv-round"
                value={predictor.roundIdx}
                onChange={(e) => predictor.setRoundIdx(Number(e.target.value))}
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100
                           outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              >
                {Object.entries(ROUND_LABELS).map(([idx, label]) => (
                  <option key={idx} value={idx}>{label}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="adv-draw-size" className="text-sm font-medium text-slate-300">Draw size</label>
              <input
                id="adv-draw-size"
                type="number"
                min="4"
                step="4"
                value={predictor.drawSize}
                onChange={(e) => predictor.setDrawSize(e.target.value)}
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100
                           outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="adv-best-of" className="text-sm font-medium text-slate-300">Best of</label>
              <select
                id="adv-best-of"
                value={predictor.bestOf}
                onChange={(e) => predictor.setBestOf(Number(e.target.value))}
                className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100
                           outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              >
                <option value={3}>3</option>
                <option value={5}>5</option>
              </select>
            </div>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={predictor.predict}
        disabled={!predictor.canSubmit}
        className="mt-6 w-full rounded-lg bg-emerald-600 px-4 py-3 font-semibold text-white transition
                   hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
      >
        {predictor.loading ? 'Calculating…' : 'Predict Winner'}
      </button>
    </div>
  )
}
