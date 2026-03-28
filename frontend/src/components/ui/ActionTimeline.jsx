import { useState } from 'react'

const TYPE_CONFIG = {
  meal: { icon: 'restaurant', label: 'Pasto', color: 'bg-orange-100 text-orange-600' },
  trip: { icon: 'directions_car', label: 'Viaggio', color: 'bg-blue-100 text-blue-600' },
  grocery: { icon: 'shopping_cart', label: 'Spesa', color: 'bg-green-100 text-green-700' },
  clothing: { icon: 'checkroom', label: 'Vestiti', color: 'bg-purple-100 text-purple-600' },
  appliance: { icon: 'dishwasher', label: 'Elettrodomestico', color: 'bg-amber-100 text-amber-700' },
}

function ActionTimelineItem({ action }) {
  const [expanded, setExpanded] = useState(false)
  const config = TYPE_CONFIG[action.action_type] || TYPE_CONFIG[action.type] || {
    icon: 'eco',
    label: action.action_type || action.type || 'Azione',
    color: 'bg-primary-fixed/30 text-primary',
  }

  const co2 = action.co2_kg ?? action.co2_delta_kg ?? 0
  const time = action.created_at
    ? new Date(action.created_at).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
    : null
  const description = action.description || action.metadata?.description || config.label

  return (
    <button
      onClick={() => setExpanded(!expanded)}
      className="flex items-start gap-3 w-full text-left"
    >
      {/* Timeline dot & line */}
      <div className="flex flex-col items-center">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${config.color}`}>
          <span className="material-symbols-outlined text-lg">{config.icon}</span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-4 border-b border-outline-variant/20 last:border-0">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-on-surface truncate">{description}</p>
          <span className="text-xs font-bold text-on-surface/70 shrink-0 ml-2">
            +{co2.toFixed(1)} kg
          </span>
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          {time && (
            <span className="text-[11px] text-on-surface/40">{time}</span>
          )}
          <span className="text-[11px] text-on-surface/40">{config.label}</span>
        </div>
        {expanded && action.metadata && (
          <div className="mt-2 text-xs text-on-surface/50 bg-surface-container-high rounded-lg p-2">
            {Object.entries(action.metadata).map(([k, v]) => (
              <p key={k}><span className="font-medium">{k}:</span> {String(v)}</p>
            ))}
          </div>
        )}
      </div>
    </button>
  )
}

export default function ActionTimeline({ actions = [], isLoading }) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="skeleton w-9 h-9 rounded-xl" />
            <div className="flex-1">
              <div className="skeleton h-4 w-3/4 mb-1" />
              <div className="skeleton h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!actions || actions.length === 0) {
    return (
      <div className="flex flex-col items-center py-6 text-center">
        <div className="w-12 h-12 rounded-2xl bg-surface-container-high flex items-center justify-center mb-3">
          <span className="material-symbols-outlined text-on-surface/30 text-2xl">photo_camera</span>
        </div>
        <p className="text-sm text-on-surface/50">
          Nessuna azione registrata oggi.
        </p>
        <p className="text-sm text-on-surface/50">
          Inizia a tracciare!
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {actions.map((action, i) => (
        <ActionTimelineItem key={action.id || action.action_id || i} action={action} />
      ))}
    </div>
  )
}
