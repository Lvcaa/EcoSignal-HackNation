import { useNavigate, useOutletContext } from 'react-router-dom'
import ProgressDots from '../../components/onboarding/ProgressDots'
import SelectionCard from '../../components/ui/SelectionCard'

const options = [
  { value: 0, icon: 'home', title: 'Smart working', subtitle: 'Lavoro da casa' },
  { value: 1, icon: 'event', title: '1 giorno', subtitle: 'Occasionale' },
  { value: 2, icon: 'event', title: '2 giorni', subtitle: 'Occasionale' },
  { value: 3, icon: 'work', title: '3 giorni', subtitle: 'Part-time' },
  { value: 4, icon: 'work', title: '4 giorni', subtitle: 'Part-time' },
  { value: 5, icon: 'business_center', title: '5 giorni', subtitle: 'Full-time' },
  { value: 6, icon: 'local_fire_department', title: '6 giorni', subtitle: 'Intenso' },
  { value: 7, icon: 'local_fire_department', title: '7 giorni', subtitle: 'Intenso' },
]

export default function CommuteStep() {
  const navigate = useNavigate()
  const { data, updateData } = useOutletContext()

  return (
    <div className="flex flex-col h-full">
      <ProgressDots current={2} total={6} />

      <h2 className="text-2xl font-black text-on-surface mb-2 mt-2">
        Quanti giorni alla settimana vai al lavoro?
      </h2>
      <p className="text-sm text-on-surface/50 mb-6">
        La frequenza del pendolarismo influisce molto sulla tua impronta di carbonio.
      </p>

      <div className="grid grid-cols-2 gap-3">
        {options.map((opt) => (
          <SelectionCard
            key={opt.value}
            icon={opt.icon}
            title={opt.title}
            subtitle={opt.subtitle}
            selected={data.commute_days_per_week === opt.value}
            onClick={() => updateData({ commute_days_per_week: opt.value })}
          />
        ))}
      </div>

      <div className="mt-auto pt-6 flex items-center justify-between">
        <button onClick={() => navigate('/onboarding/transport')} className="text-on-surface/50 text-sm font-medium">
          Indietro
        </button>
        <button
          onClick={() => navigate('/onboarding/diet')}
          disabled={data.commute_days_per_week === undefined}
          className="bg-primary text-on-primary font-bold px-8 py-3 rounded-2xl active:scale-95 transition-all ease-out-expo disabled:opacity-40 flex items-center gap-2"
        >
          Prossimo <span className="material-symbols-outlined text-lg">arrow_forward</span>
        </button>
      </div>
    </div>
  )
}
