export default function AboutModel() {
  return (
    <section className="mx-auto mt-10 max-w-2xl px-4 text-center">
      <h2 className="text-lg font-semibold text-slate-200">About the model</h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-400">
        A custom three-part Elo system (overall match, serve, and return ratings) is blended
        by surface and decayed over time for inactive players, then combined with rolling
        52-week form stats and head-to-head history. The model is a gradient-boosted classifier,
        evaluated with time-series cross-validation so future matches never leak into training.
      </p>
    </section>
  )
}
