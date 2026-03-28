import { useNavigate, useOutletContext } from 'react-router-dom'
import ProgressDots from '../../components/onboarding/ProgressDots'
import SelectionCard from '../../components/ui/SelectionCard'

const options = [
  { value: 'car', icon: 'directions_car', title: 'Car', subtitle: 'Commuter/Sedan' },
  { value: 'transit', icon: 'directions_bus', title: 'Public transit', subtitle: 'Bus, Train, Metro' },
  { value: 'bike', icon: 'pedal_bike', title: 'Bike', subtitle: 'Cycle or E-bike' },
  { value: 'walk', icon: 'directions_walk', title: 'On foot', subtitle: 'Walking or Running' },
  { value: 'mixed', icon: 'all_inclusive', title: 'Mix', subtitle: 'Variable options' },
]

export default function TransportStep() {
  const navigate = useNavigate()
  const { data, updateData } = useOutletContext()

  return (
    <div className="flex flex-col h-full">
      <ProgressDots current={1} total={6} />

      <h2 className="text-2xl font-black text-on-surface mb-2 mt-2">How do you get around?</h2>
      <p className="text-sm text-on-surface/50 mb-6">
        This helps us estimate your daily carbon footprint with precision.
      </p>

      <div className="grid grid-cols-2 gap-3">
        {options.slice(0, 4).map((opt) => (
          <SelectionCard
            key={opt.value}
            icon={opt.icon}
            title={opt.title}
            subtitle={opt.subtitle}
            selected={data.transport_mode === opt.value}
            onClick={() => updateData({ transport_mode: opt.value })}
          />
        ))}
      </div>
      <div className="mt-3">
        <SelectionCard
          icon={options[4].icon}
          title={options[4].title}
          subtitle={options[4].subtitle}
          selected={data.transport_mode === 'mixed'}
          onClick={() => updateData({ transport_mode: 'mixed' })}
        />
      </div>

      {/* AI insight */}
      <div className="mt-6 p-4 rounded-2xl bg-tertiary-fixed/50">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-on-tertiary-fixed-variant text-lg">auto_awesome</span>
          <p className="text-sm text-on-tertiary-fixed">
            Commuters using public transit reduce their personal CO2 emissions by up to{' '}
            <span className="font-bold text-primary">45%</span> annually.
          </p>
        </div>
      </div>

      <div className="mt-auto pt-6 flex items-center justify-between">
        <button onClick={() => navigate('/onboarding/zip')} className="text-on-surface/50 text-sm font-medium">
          Back
        </button>
        <button
          onClick={() => navigate('/onboarding/commute')}
          className="bg-primary text-on-primary font-bold px-8 py-3 rounded-2xl active:scale-95 transition-all ease-out-expo flex items-center gap-2"
        >
          Next <span className="material-symbols-outlined text-lg">arrow_forward</span>
        </button>
      </div>
    </div>
  )
}
