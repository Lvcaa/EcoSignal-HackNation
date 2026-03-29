import { useFootprintHistory, useWeeklySummary, useStreak } from '../hooks/useDashboard'

const DAYS = ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM']

const ACTION_TYPE_LABELS = {
  meal: 'Pasti',
  trip: 'Trasporti',
  grocery: 'Spesa',
  clothing: 'Abbigliamento',
  appliance: 'Elettrodomestici',
}

const ACTION_TYPE_ICONS = {
  meal: 'restaurant',
  trip: 'directions_car',
  grocery: 'shopping_cart',
  clothing: 'checkroom',
  appliance: 'dishwasher',
}

export default function Progress() {
  const history = useFootprintHistory(4)
  const weekly = useWeeklySummary()
  const streak = useStreak()

  const weeks = history.data?.weeks || history.data || []
  const weeksArr = Array.isArray(weeks) ? weeks : []
  const maxKg = Math.max(...weeksArr.map((w) => w.kg_co2 || w.total_kg_co2 || 0), 1)

  const streakDays = streak.data?.current_streak ?? 0
  const totalCompletions = streak.data?.total_completions ?? 0

  // Weekly calendar: determine which days of current week have activities
  const activeDays = new Set(weekly.data?.active_days || [])
  const today = new Date()
  const dayOfWeek = today.getDay() === 0 ? 6 : today.getDay() - 1 // Mon=0
  const mondayDate = new Date(today)
  mondayDate.setDate(today.getDate() - dayOfWeek)

  // Compute stats from history
  const weeklyKgs = weeksArr.map((w) => w.kg_co2 || w.total_kg_co2 || 0)
  const avgWeekly = weeklyKgs.length > 0
    ? (weeklyKgs.reduce((a, b) => a + b, 0) / weeklyKgs.length).toFixed(1)
    : '—'
  const bestReduction = weeklyKgs.length >= 2
    ? Math.min(...weeklyKgs.slice(1).map((v, i) => v - weeklyKgs[i])).toFixed(1)
    : '—'

  // Weekly summary entries
  const entries = weekly.data?.entries || []
  const weeklyTotal = weekly.data?.total_co2_delta_kg ?? 0

  return (
    <div className="pb-4 px-4">
      {/* Hero streak card */}
      <div className="mt-4 bg-gradient-to-br from-primary to-primary-container rounded-3xl p-6 text-on-primary text-center">
        <p className="text-[10px] uppercase tracking-[0.2em] font-bold bg-white/20 inline-block px-3 py-1 rounded-full mb-3">
          Attivit&agrave; Giornaliera
        </p>
        {streak.isLoading ? (
          <div className="skeleton h-16 w-32 mx-auto rounded-xl" />
        ) : (
          <>
            <div className="flex items-center justify-center gap-2 mb-2">
              <span className="text-3xl">{streakDays > 0 ? '🔥' : '💤'}</span>
              <span className="text-5xl font-black">{streakDays}</span>
              <span className="text-2xl font-bold">giorni</span>
            </div>
            <p className="text-sm opacity-80">
              {streakDays === 0
                ? 'Registra la tua prima attivit\u00e0 per iniziare!'
                : streakDays === 1
                  ? 'Ottimo inizio! Continua domani per allungare la serie.'
                  : `${totalCompletions} attivit\u00e0 totali registrate.`}
            </p>
          </>
        )}
      </div>

      {/* Weekly calendar */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-on-surface">Registro Settimanale</h3>
          <span className="text-xs text-primary font-bold">
            {mondayDate.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })} – {new Date(mondayDate.getTime() + 6 * 86400000).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })}
          </span>
        </div>
        <div className="flex justify-between">
          {DAYS.map((day, i) => {
            const d = new Date(mondayDate)
            d.setDate(mondayDate.getDate() + i)
            const iso = d.toISOString().slice(0, 10)
            const isToday = i === dayOfWeek
            const isFuture = i > dayOfWeek
            const hasActivity = activeDays.has(iso)
            return (
              <div key={day} className="flex flex-col items-center gap-1.5">
                <span className="text-[10px] font-medium text-on-surface/40">{day}</span>
                <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                  isToday && hasActivity
                    ? 'bg-primary text-on-primary'
                    : isToday
                      ? 'ring-2 ring-primary bg-surface-container-high text-on-surface/50'
                      : hasActivity
                        ? 'bg-primary text-on-primary'
                        : isFuture
                          ? 'bg-surface-container text-on-surface/20'
                          : 'bg-surface-container-high text-on-surface/30'
                }`}>
                  {hasActivity ? (
                    <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check</span>
                  ) : isFuture ? (
                    <span className="text-xs font-medium">{d.getDate()}</span>
                  ) : (
                    <span className="material-symbols-outlined text-sm">close</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Weekly activity breakdown */}
      <div className="mt-6 bg-surface-container-lowest rounded-2xl shadow-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-on-surface">Attivit&agrave; della Settimana</h3>
          <span className="text-xs font-bold text-primary">{weeklyTotal.toFixed(1)} kg CO₂</span>
        </div>

        {weekly.isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="skeleton h-12 rounded-xl" />)}
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-6">
            <span className="material-symbols-outlined text-3xl text-on-surface/20 mb-2">eco</span>
            <p className="text-sm text-on-surface/40">Nessuna attivit&agrave; registrata questa settimana.</p>
            <p className="text-xs text-on-surface/30 mt-1">Inizia a registrare pasti, trasporti o spesa!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => (
              <div key={entry.action_type} className="flex items-center gap-3 p-3 rounded-xl bg-surface-container">
                <div className="w-10 h-10 rounded-xl bg-primary-fixed/30 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-primary text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                    {ACTION_TYPE_ICONS[entry.action_type] || 'eco'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-on-surface">
                    {ACTION_TYPE_LABELS[entry.action_type] || entry.action_type}
                  </p>
                  <p className="text-xs text-on-surface/50">
                    {entry.count} {entry.count === 1 ? 'registrazione' : 'registrazioni'}
                  </p>
                </div>
                <span className="text-sm font-bold text-on-surface">
                  {entry.total_co2_delta_kg.toFixed(1)} kg
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Emission trend */}
      <div className="mt-6 bg-surface-container-lowest rounded-2xl shadow-card p-5">
        <h3 className="font-bold text-on-surface">Tendenza Emissioni</h3>
        <p className="text-xs text-on-surface/40 mt-0.5">
          Andamento kg CO₂ nelle ultime 4 settimane
        </p>

        {history.isLoading ? (
          <div className="skeleton h-32 mt-4" />
        ) : weeksArr.length === 0 ? (
          <div className="text-center py-8">
            <span className="material-symbols-outlined text-3xl text-on-surface/20">show_chart</span>
            <p className="text-sm text-on-surface/40 mt-2">Non ci sono ancora dati sufficienti.</p>
          </div>
        ) : (
          <>
            <div className="flex items-end justify-between gap-3 mt-6 h-28">
              {weeksArr.slice(-4).map((w, i, arr) => {
                const kg = w.kg_co2 || w.total_kg_co2 || 0
                const pct = (kg / maxKg) * 100
                const isLast = i === arr.length - 1
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2">
                    <span className="text-[10px] font-bold text-on-surface/60">{kg.toFixed(1)}</span>
                    <div className="w-full flex justify-center">
                      <div
                        className={`w-10 rounded-xl transition-all duration-700 ease-out-expo ${
                          isLast ? 'bg-primary' : 'bg-surface-container-high'
                        }`}
                        style={{ height: `${Math.max(pct, 8)}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-medium text-on-surface/40">
                      {w.label || (isLast ? 'OGGI' : `S-${arr.length - i - 1}`)}
                    </span>
                  </div>
                )
              })}
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t border-outline-variant/20">
              <div className="text-center">
                <p className="text-[10px] uppercase text-on-surface/40 font-bold tracking-wider">Miglior Riduzione</p>
                <p className="text-xl font-black text-primary">
                  {typeof bestReduction === 'number' || (bestReduction !== '—')
                    ? `${bestReduction}kg`
                    : '—'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-[10px] uppercase text-on-surface/40 font-bold tracking-wider">Media Settimanale</p>
                <p className="text-xl font-black text-on-surface">
                  {avgWeekly !== '—' ? `${avgWeekly}kg` : '—'}
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
