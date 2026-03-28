import { useNavigate, useOutletContext } from 'react-router-dom'
import ProgressDots from '../../components/onboarding/ProgressDots'
import SelectionCard from '../../components/ui/SelectionCard'

const petTypes = [
  { value: 'dog', icon: 'pets', title: 'Cane', subtitle: '~4.2 kg CO₂/settimana' },
  { value: 'cat', icon: 'pets', title: 'Gatto', subtitle: '~2.1 kg CO₂/settimana' },
  { value: 'small_animal', icon: 'cruelty_free', title: 'Piccolo animale', subtitle: '~0.5 kg CO₂/settimana' },
]

export default function PetStep() {
  const navigate = useNavigate()
  const { data, updateData, handleFinish, submitting } = useOutletContext()

  const hasPets = data.has_pets

  return (
    <div className="flex flex-col h-full">
      <ProgressDots current={5} total={6} />

      <h2 className="text-2xl font-black text-on-surface mb-2 mt-2">
        Hai animali domestici?
      </h2>
      <p className="text-sm text-on-surface/50 mb-6">
        Gli animali domestici hanno un impatto ambientale legato al cibo e alle cure.
      </p>

      <div className="grid grid-cols-2 gap-3 mb-6">
        <SelectionCard
          icon="check_circle"
          title="Sì"
          subtitle="Ho animali"
          selected={hasPets === true}
          onClick={() => updateData({ has_pets: true, pet_type: data.pet_type || 'dog', pet_count: data.pet_count || 1 })}
        />
        <SelectionCard
          icon="cancel"
          title="No"
          subtitle="Nessun animale"
          selected={hasPets === false}
          onClick={() => updateData({ has_pets: false, pet_type: null, pet_count: 0 })}
        />
      </div>

      {hasPets && (
        <>
          <label className="text-[10px] font-bold text-on-surface/50 uppercase tracking-wider mb-2">
            Tipo di animale
          </label>
          <div className="grid grid-cols-3 gap-3 mb-4">
            {petTypes.map((opt) => (
              <SelectionCard
                key={opt.value}
                icon={opt.icon}
                title={opt.title}
                subtitle={opt.subtitle}
                selected={data.pet_type === opt.value}
                onClick={() => updateData({ pet_type: opt.value })}
              />
            ))}
          </div>

          <label className="text-[10px] font-bold text-on-surface/50 uppercase tracking-wider mb-2">
            Quanti? ({data.pet_count || 1})
          </label>
          <div className="flex items-center gap-4">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                onClick={() => updateData({ pet_count: n })}
                className={`w-10 h-10 rounded-xl font-bold text-sm transition-all duration-300 ease-out-expo ${
                  data.pet_count === n
                    ? 'bg-primary text-on-primary shadow-card-lg'
                    : 'bg-surface-container-lowest border-2 border-outline-variant/30 text-on-surface'
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        </>
      )}

      <div className="mt-auto pt-6">
        <button
          onClick={() => navigate('/onboarding/home')}
          className="text-on-surface/50 text-sm font-medium mb-3 block"
        >
          Indietro
        </button>
        <button
          onClick={handleFinish}
          disabled={hasPets === undefined || submitting}
          className="w-full bg-primary text-on-primary font-bold py-4 rounded-2xl active:scale-95 transition-all ease-out-expo disabled:opacity-50 text-lg"
        >
          {submitting ? 'Calcolo in corso...' : 'Scopri la tua impronta'}
        </button>
      </div>
    </div>
  )
}
