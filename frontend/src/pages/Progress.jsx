import { useFootprintHistory } from '../hooks/useDashboard'
import { useQuery } from '@tanstack/react-query'
import { getActions } from '../api/actions'

const DAYS = ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM']

export default function Progress() {
  const history = useFootprintHistory(4)
  const actionsQuery = useQuery({
    queryKey: ['actions'],
    queryFn: () => getActions().then((r) => r.data),
  })

  const weeks = history.data?.weeks || history.data || []
  const maxKg = Math.max(...(Array.isArray(weeks) ? weeks.map((w) => w.kg_co2 || w.total_kg_co2 || 0) : [10]), 1)

  // Derive streak from actions data
  const streakDays = actionsQuery.data?.streak_days ?? 9

  return (
    <div className="pb-4 px-4">
      {/* Hero streak card */}
      <div className="mt-4 bg-gradient-to-br from-primary to-primary-container rounded-3xl p-6 text-on-primary text-center">
        <p className="text-[10px] uppercase tracking-[0.2em] font-bold bg-white/20 inline-block px-3 py-1 rounded-full mb-3">
          Attivit&agrave; Giornaliera
        </p>
        <div className="flex items-center justify-center gap-2 mb-2">
          <span className="text-3xl">🔥</span>
          <span className="text-5xl font-black">{streakDays}</span>
          <span className="text-2xl font-bold">giorni</span>
        </div>
        <p className="text-sm opacity-80">
          Continua cos&igrave;! Sei nel 5% degli utenti pi&ugrave; costanti.
        </p>
      </div>

      {/* Weekly calendar */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-on-surface">Registro Settimanale</h3>
          <span className="text-xs text-primary font-bold">Settimana 12</span>
        </div>
        <div className="flex justify-between">
          {DAYS.map((day, i) => {
            const completed = i !== 3 // mock: all except Thursday
            const isToday = i === 6
            return (
              <div key={day} className="flex flex-col items-center gap-1.5">
                <span className="text-[10px] font-medium text-on-surface/40">{day}</span>
                <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                  isToday
                    ? 'bg-primary text-on-primary'
                    : completed
                      ? 'bg-primary text-on-primary'
                      : 'bg-surface-container-high text-on-surface/30'
                }`}>
                  {isToday ? (
                    <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  ) : completed ? (
                    <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check</span>
                  ) : (
                    <span className="material-symbols-outlined text-sm">close</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Milestone badge */}
      <div className="mt-6 bg-surface-container-lowest rounded-2xl shadow-card p-5 flex items-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-primary-fixed/30 flex items-center justify-center shrink-0">
          <div className="relative">
            <span className="material-symbols-outlined text-primary text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
              military_tech
            </span>
            <span className="absolute -bottom-1 -right-1 text-[8px] font-black bg-primary text-on-primary px-1.5 py-0.5 rounded-full">
              LVL 4
            </span>
          </div>
        </div>
        <div>
          <p className="font-bold text-on-surface">Carbon Cutter</p>
          <p className="text-xs text-on-surface/50 mt-0.5">
            Hai risparmiato <span className="font-bold text-primary">20 kg CO₂</span> questo mese. Sei un eroe per il pianeta!
          </p>
        </div>
      </div>

      {/* Emission trend */}
      <div className="mt-6 bg-surface-container-lowest rounded-2xl shadow-card p-5">
        <h3 className="font-bold text-on-surface">Tendenza Emissioni</h3>
        <p className="text-xs text-on-surface/40 mt-0.5">
          Andamento kg CO₂ nelle ultime 4 settimane
        </p>

        {history.isLoading ? (
          <div className="skeleton h-32 mt-4" />
        ) : (
          <>
            <div className="flex items-end justify-between gap-3 mt-6 h-28">
              {(Array.isArray(weeks) && weeks.length > 0 ? weeks : [
                { label: 'S-4', kg_co2: 8 },
                { label: 'S-3', kg_co2: 7.2 },
                { label: 'S-2', kg_co2: 6.5 },
                { label: 'OGGI', kg_co2: 5.2 },
              ]).slice(-4).map((w, i) => {
                const kg = w.kg_co2 || w.total_kg_co2 || 0
                const pct = (kg / maxKg) * 100
                const labels = ['S-4', 'S-3', 'S-2', 'OGGI']
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full flex justify-center">
                      <div
                        className={`w-10 rounded-xl transition-all duration-700 ease-out-expo ${
                          i === 3 ? 'bg-primary' : 'bg-surface-container-high'
                        }`}
                        style={{ height: `${Math.max(pct, 8)}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-medium text-on-surface/40">{w.label || labels[i]}</span>
                  </div>
                )
              })}
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t border-outline-variant/20">
              <div className="text-center">
                <p className="text-[10px] uppercase text-on-surface/40 font-bold tracking-wider">Miglior Riduzione</p>
                <p className="text-xl font-black text-primary">-12.4kg</p>
              </div>
              <div className="text-center">
                <p className="text-[10px] uppercase text-on-surface/40 font-bold tracking-wider">Media Settimanale</p>
                <p className="text-xl font-black text-on-surface">5.2kg</p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* AI Insight */}
      <div className="mt-4 p-4 rounded-2xl bg-secondary-fixed/30">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-secondary/10 flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-secondary text-lg">auto_awesome</span>
          </div>
          <div>
            <p className="text-sm font-bold text-on-surface">Suggerimento AI</p>
            <p className="text-xs text-on-surface/60 mt-1">
              Dalle tue tendenze, potresti risparmiare altri <span className="font-bold">3kg CO₂</span> preferendo la bici nei weekend.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
