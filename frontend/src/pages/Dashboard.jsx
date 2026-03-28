import CircularProgress from '../components/ui/CircularProgress'
import AirAlertBanner from '../components/ui/AirAlertBanner'
import NarrativeCard from '../components/ui/NarrativeCard'
import ActionCard from '../components/ui/ActionCard'
import { useNavigate } from 'react-router-dom'
import { useFootprint, useAirQuality, useNarrative, useActions, useCompleteAction, useLatestSurvey } from '../hooks/useDashboard'

function getWeekStart() {
  const now = new Date()
  const day = now.getDay()
  const diff = day === 0 ? 6 : day - 1
  const monday = new Date(now)
  monday.setDate(now.getDate() - diff)
  return monday.toISOString().slice(0, 10)
}

export default function Dashboard() {
  const navigate = useNavigate()
  const footprint = useFootprint()
  const airQuality = useAirQuality()
  const narrative = useNarrative()
  const actions = useActions()
  const completeAction = useCompleteAction()
  const latestSurvey = useLatestSurvey()

  const surveyThisWeek = latestSurvey.data?.week_start === getWeekStart()

  const fp = footprint.data
  const totalKg = fp?.total_kg_co2 ?? 0
  const pctVsAvg = fp?.vs_national_avg_pct ?? 0
  const ringValue = Math.min(100, Math.max(0, ((100 + pctVsAvg) / 200) * 100))

  return (
    <div className="pb-4">
      {/* Air Alert */}
      <AirAlertBanner data={airQuality.data} />

      {/* Weekly Footprint */}
      <section className="px-4 mt-6">
        <p className="text-[10px] font-bold text-on-surface/40 uppercase tracking-[0.2em] text-center mb-4">
          Weekly Footprint
        </p>

        {footprint.isLoading ? (
          <div className="flex justify-center"><div className="skeleton w-48 h-48 rounded-full" /></div>
        ) : (
          <div className="flex flex-col items-center">
            <CircularProgress value={ringValue} size={192}>
              <span className="text-4xl font-black text-on-surface">{totalKg.toFixed(0)}</span>
              <span className="text-xs text-on-surface/50 -mt-1">kg CO₂</span>
            </CircularProgress>

            <p className="mt-3 text-sm font-medium text-on-surface/70">
              {pctVsAvg < 0 ? `${pctVsAvg}%` : `+${pctVsAvg}%`} vs last week{' '}
              {pctVsAvg <= 0 && <span className="text-primary">🌿</span>}
            </p>

            <div className="flex gap-2 mt-3">
              {['Transport', 'Food', 'Home'].map((cat) => (
                <span
                  key={cat}
                  className="text-[11px] font-medium px-3 py-1 rounded-full bg-surface-container-high text-on-surface/60 flex items-center gap-1"
                >
                  <span className="material-symbols-outlined text-xs">
                    {cat === 'Transport' ? 'directions_bus' : cat === 'Food' ? 'restaurant' : 'home'}
                  </span>
                  {cat}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* AI Narrative */}
      <NarrativeCard data={narrative.data} isLoading={narrative.isLoading} />

      {/* Weekly Survey */}
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
                {latestSurvey.data.co2_breakdown.total_kg.toFixed(1)} kg CO&#x2082;
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

      {/* Actions */}
      <section className="px-4 mt-6">
        <h3 className="text-lg font-bold text-on-surface mb-3">Your next steps</h3>

        {actions.isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="skeleton h-20 w-full" />)}
          </div>
        ) : actions.error ? (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200">
            <p className="text-sm text-red-600">Dati temporaneamente non disponibili</p>
            <button onClick={() => actions.refetch()} className="text-xs text-red-500 mt-1 font-medium">
              Riprova
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {(actions.data?.actions || actions.data || []).slice(0, 3).map((action) => (
              <ActionCard
                key={action.action_id}
                action={action}
                onComplete={(id) => completeAction.mutate(id)}
                completing={completeAction.isPending}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
