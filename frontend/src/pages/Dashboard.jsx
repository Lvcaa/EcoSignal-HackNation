import { useState } from 'react'
import CircularProgress from '../components/ui/CircularProgress'
import AirAlertBanner from '../components/ui/AirAlertBanner'
import NarrativeCard from '../components/ui/NarrativeCard'
import ActionTimeline from '../components/ui/ActionTimeline'
import AddressFixDialog from '../components/ui/AddressFixDialog'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { useFootprint, useAirQuality, useNarrative, useWeeklySummary, useMonthlySummary, useLatestSurvey, useTodayActions } from '../hooks/useDashboard'

function getWeekStart() {
  const now = new Date()
  const day = now.getDay()
  const diff = day === 0 ? 6 : day - 1
  const monday = new Date(now)
  monday.setDate(now.getDate() - diff)
  return monday.toISOString().slice(0, 10)
}

const quickActions = [
  { icon: 'restaurant', label: 'Pasto', to: '/actions/meal' },
  { icon: 'directions_car', label: 'Viaggio', to: '/actions/trip' },
  { icon: 'shopping_cart', label: 'Spesa', to: '/actions/grocery' },
  { icon: 'checkroom', label: 'Vestiti', to: '/actions/clothing' },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const { latitude, longitude } = useAuthStore()
  const [showAddressFix, setShowAddressFix] = useState(!latitude || !longitude)
  const [totalsPeriod, setTotalsPeriod] = useState('weekly')
  const footprint = useFootprint()
  const airQuality = useAirQuality()
  const narrative = useNarrative()
  const weeklySummary = useWeeklySummary()
  const monthlySummary = useMonthlySummary()
  const latestSurvey = useLatestSurvey()
  const todayActions = useTodayActions()

  const surveyThisWeek = latestSurvey.data?.week_start === getWeekStart()

  const fp = footprint.data
  const baselineWeeklyKg = fp?.total_kg_co2 ?? 0

  // Compute current CO2 and scaled baseline based on selected period
  const todayTotal = (Array.isArray(todayActions.data) ? todayActions.data : todayActions.data?.actions ?? [])
    .reduce((s, a) => s + (a.co2_delta_kg || 0), 0)
  const currentKg =
    totalsPeriod === 'daily' ? todayTotal
    : totalsPeriod === 'weekly' ? (weeklySummary.data?.total_co2_delta_kg ?? 0)
    : (monthlySummary.data?.total_co2_delta_kg ?? 0)
  const baselineKg =
    totalsPeriod === 'daily' ? baselineWeeklyKg / 7
    : totalsPeriod === 'weekly' ? baselineWeeklyKg
    : baselineWeeklyKg * 4.33
  const periodLabel =
    totalsPeriod === 'daily' ? 'oggi' : totalsPeriod === 'weekly' ? 'settimana' : 'mese'

  // Comparison logic
  const deltaPct = baselineKg > 0
    ? ((currentKg - baselineKg) / baselineKg) * 100
    : 0
  const isBelow = deltaPct <= 0
  const ringColor = deltaPct <= 0 ? 'green' : deltaPct <= 20 ? 'orange' : 'red'

  // Ring values: baseline as outer, current as inner (both normalized to 0-100)
  const maxKg = Math.max(baselineKg, currentKg, 1)
  const currentRingValue = (currentKg / maxKg) * 100
  const baselineRingValue = (baselineKg / maxKg) * 100

  return (
    <div className="pb-4">
      {/* Address fix dialog */}
      {showAddressFix && <AddressFixDialog onClose={() => setShowAddressFix(false)} />}

      {/* Air Alert */}
      <AirAlertBanner data={airQuality.data ?? { aqi_label: 'good', pm25: null, city: '' }} />

      {/* CO2 Comparison Card */}
      <section className="px-4 mt-6">
        <p className="text-[10px] font-bold text-on-surface/40 uppercase tracking-[0.2em] text-center mb-3">
          Il tuo impatto
        </p>
        <div className="flex justify-center mb-4">
          <div className="flex gap-1 bg-surface-container-high rounded-full p-0.5">
            {['daily', 'weekly', 'monthly'].map((p) => (
              <button
                key={p}
                onClick={() => setTotalsPeriod(p)}
                className={`text-[11px] font-bold px-4 py-1.5 rounded-full transition-all ${
                  totalsPeriod === p
                    ? 'bg-primary text-on-primary'
                    : 'text-on-surface/50'
                }`}
              >
                {p === 'daily' ? 'Today' : p === 'weekly' ? 'Week' : 'Month'}
              </button>
            ))}
          </div>
        </div>

        {footprint.isLoading ? (
          <div className="flex justify-center"><div className="skeleton w-48 h-48 rounded-full" /></div>
        ) : (
          <div className="flex flex-col items-center">
            <CircularProgress
              value={currentRingValue}
              baselineValue={baselineRingValue}
              size={192}
              colorClass={ringColor}
            >
              <span className="text-4xl font-black text-on-surface">{currentKg.toFixed(1)}</span>
              <span className="text-xs text-on-surface/50 -mt-1">kg CO₂</span>
            </CircularProgress>

            <div className="mt-3 text-center">
              <p className="text-sm font-medium text-on-surface/70">
                Baseline: {baselineKg.toFixed(1)} kg/{periodLabel}
              </p>
              <p className={`text-sm font-bold mt-1 ${isBelow ? 'text-primary' : ringColor === 'red' ? 'text-red-600' : 'text-amber-600'}`}>
                {isBelow ? '' : '+'}{deltaPct.toFixed(0)}% rispetto alla tua baseline
                {isBelow && ' 🌿'}
              </p>
            </div>
          </div>
        )}
      </section>

      {/* CO2 Totals Card */}
      <section className="px-4 mt-6">
        <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-on-surface">CO₂ Breakdown</h3>
            <span className="text-[10px] font-bold text-primary bg-primary-fixed/30 px-2 py-0.5 rounded-full uppercase">
              {totalsPeriod === 'daily' ? 'Today' : totalsPeriod === 'weekly' ? 'This week' : 'This month'}
            </span>
          </div>
          {(() => {
            const source =
              totalsPeriod === 'daily' ? todayActions
              : totalsPeriod === 'weekly' ? weeklySummary
              : monthlySummary
            if (source.isLoading) return <div className="skeleton h-20 w-full rounded-xl" />
            const total =
              totalsPeriod === 'daily'
                ? (Array.isArray(source.data) ? source.data : source.data?.actions ?? []).reduce((s, a) => s + (a.co2_delta_kg || 0), 0)
                : source.data?.total_co2_delta_kg ?? 0
            const entries = totalsPeriod === 'daily' ? [] : (source.data?.entries ?? [])
            const CATEGORY_META = {
              meal: { icon: 'restaurant', label: 'Pasti', color: 'text-green-600' },
              trip: { icon: 'directions_car', label: 'Trasporti', color: 'text-blue-600' },
              grocery: { icon: 'shopping_cart', label: 'Spesa', color: 'text-amber-600' },
              clothing: { icon: 'checkroom', label: 'Vestiti', color: 'text-purple-600' },
              appliance: { icon: 'dishwasher', label: 'Elettrodom.', color: 'text-red-500' },
            }
            return (
              <>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-3xl font-black text-on-surface">{total.toFixed(1)}</span>
                  <span className="text-sm text-on-surface/50">kg CO₂</span>
                </div>
                {entries.length > 0 && (
                  <div className="space-y-2.5">
                    {entries.map((e) => {
                      const meta = CATEGORY_META[e.action_type] || { icon: 'eco', label: e.action_type, color: 'text-on-surface' }
                      const pct = total > 0 ? (e.total_co2_delta_kg / total) * 100 : 0
                      return (
                        <div key={e.action_type} className="flex items-center gap-3">
                          <span className={`material-symbols-outlined text-lg ${meta.color}`} style={{ fontVariationSettings: "'FILL' 1" }}>
                            {meta.icon}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between text-xs font-bold mb-1">
                              <span className="text-on-surface/70">{meta.label}</span>
                              <span>{e.total_co2_delta_kg.toFixed(1)} kg</span>
                            </div>
                            <div className="h-1.5 bg-surface-container-high rounded-full overflow-hidden">
                              <div
                                className="h-full bg-primary rounded-full transition-all duration-700"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
                {totalsPeriod === 'daily' && total === 0 && (
                  <p className="text-xs text-on-surface/40 text-center">No actions logged yet today</p>
                )}
              </>
            )
          })()}
        </div>
      </section>

      {/* AI Narrative */}
      <NarrativeCard data={narrative.data} isLoading={narrative.isLoading} />

      {/* Today's Actions Timeline */}
      <section className="px-4 mt-6">
        <h3 className="text-base font-bold text-on-surface mb-3">Le azioni di oggi</h3>
        <div className="bg-surface-container-lowest rounded-2xl shadow-card p-4">
          <ActionTimeline actions={Array.isArray(todayActions.data) ? todayActions.data : todayActions.data?.actions ?? []} isLoading={todayActions.isLoading} />
        </div>
      </section>

      {/* Quick Action Buttons */}
      <section className="px-4 mt-6">
        <div className="flex justify-around">
          {quickActions.map((qa) => (
            <button
              key={qa.to}
              onClick={() => navigate(qa.to)}
              className="flex flex-col items-center gap-1.5"
            >
              <div className="w-14 h-14 rounded-2xl bg-primary-fixed/30 flex items-center justify-center active:scale-95 transition-transform">
                <span className="material-symbols-outlined text-primary text-2xl">{qa.icon}</span>
              </div>
              <span className="text-[11px] font-medium text-on-surface/60">{qa.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Weekly Survey Prompt */}
      <section className="px-4 mt-6">
        {surveyThisWeek && latestSurvey.data ? (
          <div
            className="bg-surface-container-lowest rounded-2xl shadow-card p-4 cursor-pointer"
            onClick={() => navigate('/weekly-survey')}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">check_circle</span>
                <span className="text-sm font-bold text-on-surface">Elettrodomestici</span>
              </div>
              <span className="text-sm font-bold text-on-surface">
                {latestSurvey.data.co2_breakdown.total_kg.toFixed(1)} kg CO₂
              </span>
            </div>
            <p className="text-xs text-on-surface/50 mt-1 ml-8">Questionario compilato questa settimana</p>
          </div>
        ) : (
          <button
            onClick={() => navigate('/weekly-survey')}
            className="w-full bg-primary-fixed/20 border border-primary/20 rounded-2xl p-4 text-left"
          >
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-primary text-2xl">assignment</span>
              <div>
                <p className="text-sm font-bold text-on-surface">Compila il questionario settimanale</p>
                <p className="text-xs text-on-surface/50 mt-0.5">Lavatrice e lavastoviglie - 1 minuto</p>
              </div>
            </div>
          </button>
        )}
      </section>
    </div>
  )
}
