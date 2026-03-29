const levelConfig = {
  good: { bg: 'bg-green-50', border: 'border-green-200', icon: 'eco', iconColor: 'text-green-500' },
  moderate: { bg: 'bg-amber-50', border: 'border-amber-200', icon: 'warning', iconColor: 'text-amber-500' },
  unhealthy: { bg: 'bg-amber-50', border: 'border-amber-200', icon: 'warning', iconColor: 'text-amber-500' },
  hazardous: { bg: 'bg-red-50', border: 'border-red-300', icon: 'dangerous', iconColor: 'text-red-500' },
}

export default function AirAlertBanner({ data }) {
  if (!data) return null
  const label = (data.aqi_label || 'good').toLowerCase()
  const config = levelConfig[label]
  if (!config) return null

  return (
    <div className={`${config.bg} ${config.border} border rounded-2xl p-4 mx-4 mt-4`}>
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center shrink-0">
          <span className={`material-symbols-outlined ${config.iconColor}`} style={{ fontVariationSettings: "'FILL' 1" }}>
            {config.icon}
          </span>
        </div>
        <div className="flex-1">
          <p className={`text-xs font-bold uppercase tracking-wider mb-1 ${label === 'good' ? 'text-green-700' : 'text-red-700'}`}>
            {label === 'good' ? 'Local Air Quality' : 'Local Air Alert'}
          </p>
          <p className="text-sm text-on-surface">
            Today in {data.city}: PM2.5 {data.pm25?.toFixed(0) ?? '—'} &mu;g/m&sup3;{label !== 'good' ? ' — above WHO threshold' : ''}
          </p>
        </div>
      </div>
    </div>
  )
}
