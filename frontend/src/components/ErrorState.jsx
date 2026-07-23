export default function ErrorState({ message }) {
  return (
    <div className="mt-6 rounded-2xl border border-red-900/60 bg-red-950/40 p-6 text-center">
      <p className="font-medium text-red-300">Something went wrong</p>
      <p className="mt-1 text-sm text-red-400/90">{message}</p>
    </div>
  )
}
