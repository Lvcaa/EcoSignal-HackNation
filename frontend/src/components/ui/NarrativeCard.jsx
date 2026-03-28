export default function NarrativeCard({ data, isLoading }) {
  if (isLoading) {
    return (
      <div className="mx-4 mt-4 p-5 rounded-2xl bg-secondary-fixed/30 shadow-card">
        <div className="skeleton h-4 w-3/4 mb-3" />
        <div className="skeleton h-4 w-full mb-2" />
        <div className="skeleton h-4 w-5/6" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="mx-4 mt-4 p-5 rounded-2xl bg-secondary-fixed/30 shadow-card">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-secondary/10 flex items-center justify-center shrink-0 mt-0.5">
          <span className="material-symbols-outlined text-secondary text-lg">auto_awesome</span>
        </div>
        <div>
          <p className="text-sm italic text-on-surface font-medium leading-relaxed">
            &ldquo;{data.headline || data.narrative}&rdquo;
          </p>
          <p className="text-[11px] text-on-surface/50 mt-2">
            <span className="inline-block w-1.5 h-1.5 bg-on-surface/30 rounded-full mr-1.5 align-middle" />
            {data.source_note || 'Based on ISPRA data'} &middot; Updated today
          </p>
        </div>
      </div>
    </div>
  )
}
