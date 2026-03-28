import CircularProgress from '../components/ui/CircularProgress'
import AirAlertBanner from '../components/ui/AirAlertBanner'
import NarrativeCard from '../components/ui/NarrativeCard'
import ActionTimeline from '../components/ui/ActionTimeline'
import { useNavigate } from 'react-router-dom'
import { useFootprint, useAirQuality, useNarrative, useWeeklySummary, useLatestSurvey, useTodayActions } from '../hooks/useDashboard'

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
  const footprint = useFootprint()
  const airQuality = useAirQuality()
  const narrative = useNarrative()
  const weeklySummary = useWeeklySummary()
  const latestSurvey = useLatestSurvey()
  const todayActions = useTodayActions()

  const surveyThisWeek = latestSurvey.data?.week_start === getWeekStart()

  const fp = footprint.data
  const baselineKg = fp?.total_kg_co2 ?? 0
  const currentWeekKg = weeklySummary.data?.total_co2_delta_kg ?? 0

  // Comparison logic
  const deltaPct = baselineKg > 0
    ? ((currentWeekKg - baselineKg) / baselineKg) * 100
    : 0
  const isBelow = deltaPct <= 0
  const ringColor = deltaPct <= 0 ? 'green' : deltaPct <= 20 ? 'orange' : 'red'

  // Ring values: baseline as outer, current as inner (both normalized to 0-100)
  const maxKg = Math.max(baselineKg, currentWeekKg, 1)
  const currentRingValue = (currentWeekKg / maxKg) * 100
  const baselineRingValue = (baselineKg / maxKg) * 100

  return (
    <div className="pb-4">
      {/* Air Alert */}
      <AirAlertBanner data={airQuality.data} />

      {/* CO2 Comparison Card */}
      <section className="px-4 mt-6">
        <p className="text-[10px] font-bold text-on-surface/40 uppercase tracking-[0.2em] text-center mb-4">
          Il tuo impatto
        </p>

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
              <span className="text-4xl font-black text-on-surface">{currentWeekKg.toFixed(1)}</span>
              <span className="text-xs text-on-surface/50 -mt-1">kg CO₂</span>
            </CircularProgress>

            <div className="mt-3 text-center">
              <p className="text-sm font-medium text-on-surface/70">
                Baseline: {baselineKg.toFixed(1)} kg/settimana
              </p>
              <p className={`text-sm font-bold mt-1 ${isBelow ? 'text-primary' : ringColor === 'red' ? 'text-red-600' : 'text-amber-600'}`}>
                {isBelow ? '' : '+'}{deltaPct.toFixed(0)}% rispetto alla tua baseline
                {isBelow && ' 🌿'}
              </p>
            </div>
          </div>
        )}
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
