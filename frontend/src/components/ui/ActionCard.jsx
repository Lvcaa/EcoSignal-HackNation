import confetti from 'canvas-confetti'

const effortColors = {
  easy: 'bg-primary-fixed/40 text-primary',
  medium: 'bg-amber-100 text-amber-700',
  hard: 'bg-red-100 text-red-600',
}

const categoryIcons = {
  transport: 'directions_bus',
  food: 'restaurant',
  home: 'home',
  community: 'groups',
}

export default function ActionCard({ action, onComplete, completing }) {
  const handleComplete = () => {
    confetti({
      particleCount: 60,
      spread: 50,
      origin: { y: 0.7 },
      colors: ['#146940', '#a4f4bf', '#47a1ff'],
    })
    onComplete(action.action_id)
  }

  return (
    <div className="flex items-center gap-3 p-4 bg-surface-container-lowest rounded-2xl shadow-card">
      <div className="w-10 h-10 rounded-xl bg-primary-fixed/30 flex items-center justify-center shrink-0">
        <span className="material-symbols-outlined text-primary text-xl">
          {categoryIcons[action.category] || 'eco'}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm text-on-surface">{action.title}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-primary font-medium">
            Saves ~{action.co2_saving_kg_week} kg CO₂/week
          </span>
          <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${effortColors[action.effort] || effortColors.medium}`}>
            {action.effort}
          </span>
        </div>
      </div>
      <button
        onClick={handleComplete}
        disabled={action.completed_today || completing}
        className={`w-7 h-7 rounded-full border-2 flex items-center justify-center shrink-0 transition-all active:scale-95 ${
          action.completed_today
            ? 'bg-primary border-primary text-on-primary'
            : 'border-outline-variant hover:border-primary'
        }`}
      >
        {action.completed_today && (
          <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check</span>
        )}
      </button>
    </div>
  )
}
