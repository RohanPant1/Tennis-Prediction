export default function LoadingState({ isSlow }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-slate-800
                    bg-slate-900/60 p-6 text-center shadow-xl">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-emerald-500" />
      <p className="text-slate-300">Calculating prediction…</p>
      {isSlow && (
        <p className="max-w-sm text-sm text-slate-500">
          Still working, the backend may be waking up from a cold start (can take up to 30s-1m on the first request).
        </p>
      )}
    </div>
  )
}
