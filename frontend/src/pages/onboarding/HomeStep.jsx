import { useNavigate, useOutletContext } from 'react-router-dom'
import ProgressDots from '../../components/onboarding/ProgressDots'
import SelectionCard from '../../components/ui/SelectionCard'

const homeTypes = [
  { value: 'apartment', icon: 'apartment', title: 'Appartamento', subtitle: 'Condominio o palazzo' },
  { value: 'house', icon: 'house', title: 'Casa', subtitle: 'Indipendente o bifamiliare' },
]

export default function HomeStep() {
  const navigate = useNavigate()
  const { data, updateData } = useOutletContext()

  const size = data.home_size_sqm ?? 70

  return (
    <div className="flex flex-col h-full">
      <ProgressDots current={4} total={6} />

      <h2 className="text-2xl font-black text-on-surface mb-2 mt-2">
        Com'è la tua casa?
      </h2>
      <p className="text-sm text-on-surface/50 mb-6">
        Il tipo e la dimensione della tua abitazione influenzano il consumo energetico.
      </p>

      <div className="grid grid-cols-2 gap-3 mb-6">
        {homeTypes.map((opt) => (
          <SelectionCard
            key={opt.value}
            icon={opt.icon}
            title={opt.title}
            subtitle={opt.subtitle}
            selected={data.home_type === opt.value}
            onClick={() => updateData({ home_type: opt.value })}
          />
        ))}
      </div>

      <label className="text-[10px] font-bold text-on-surface/50 uppercase tracking-wider mb-2">
        Dimensione ({size} m²)
      </label>
      <input
        type="range"
        min={10}
        max={300}
        step={5}
        value={size}
        onChange={(e) => updateData({ home_size_sqm: Number(e.target.value) })}
        className="w-full accent-primary"
      />
      <div className="flex justify-between text-xs text-on-surface/40 mt-1">
        <span>10 m²</span>
        <span>300 m²</span>
      </div>

      <div className="mt-6 p-4 rounded-2xl bg-tertiary-fixed/50">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-on-tertiary-fixed-variant text-lg">lightbulb</span>
          <p className="text-sm text-on-tertiary-fixed">
            Una casa più grande consuma in media il <span className="font-bold text-primary">40%</span> in più di energia per il riscaldamento.
          </p>
        </div>
      </div>

      <div className="mt-auto pt-6 flex items-center justify-between">
        <button onClick={() => navigate('/onboarding/diet')} className="text-on-surface/50 text-sm font-medium">
          Indietro
        </button>
        <button
          onClick={() => navigate('/onboarding/pet')}
          disabled={!data.home_type}
          className="bg-primary text-on-primary font-bold px-8 py-3 rounded-2xl active:scale-95 transition-all ease-out-expo disabled:opacity-40 flex items-center gap-2"
        >
          Prossimo <span className="material-symbols-outlined text-lg">arrow_forward</span>
        </button>
      </div>
    </div>
  )
}
