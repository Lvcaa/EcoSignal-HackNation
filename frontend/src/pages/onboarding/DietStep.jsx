import { useNavigate, useOutletContext } from 'react-router-dom'
import ProgressDots from '../../components/onboarding/ProgressDots'

const options = [
  { value: 'meat_daily', icon: 'restaurant', title: 'Meat every day', subtitle: 'High carbon intensity' },
  { value: 'meat_weekly', icon: 'lunch_dining', title: 'A few times a week', subtitle: 'Moderate carbon intensity' },
  { value: 'vegetarian', icon: 'spa', title: 'Vegetarian', subtitle: 'Lower carbon footprint' },
  { value: 'vegan', icon: 'eco', title: 'Vegan', subtitle: 'Lowest carbon footprint' },
]

export default function DietStep() {
  const navigate = useNavigate()
  const { data, updateData } = useOutletContext()

  return (
    <div className="flex flex-col h-full">
      <ProgressDots current={3} total={6} />

      <h2 className="text-2xl font-black text-on-surface mb-2 mt-2">What&apos;s your diet like?</h2>
      <p className="text-sm text-on-surface/50 mb-6">
        Food choices represent a significant part of your carbon footprint. Choose the option that best describes your habits.
      </p>

      <div className="space-y-3">
        {options.map((opt) => {
          const selected = data.diet_type === opt.value
          return (
            <button
              key={opt.value}
              onClick={() => updateData({ diet_type: opt.value })}
              className={`w-full flex items-center gap-4 p-4 rounded-2xl text-left transition-all duration-300 ease-out-expo active:scale-[0.98] ${
                selected
                  ? 'bg-primary-fixed/30 border-2 border-primary-fixed'
                  : 'bg-surface-container-lowest border-2 border-transparent shadow-card'
              }`}
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                selected ? 'bg-primary/10' : 'bg-surface-container-high'
              }`}>
                <span className={`material-symbols-outlined ${selected ? 'text-primary' : 'text-on-surface/50'}`}
                  style={{ fontVariationSettings: "'FILL' 1" }}>
                  {opt.icon}
                </span>
              </div>
              <div className="flex-1">
                <p className="font-bold text-sm text-on-surface">{opt.title}</p>
                <p className="text-xs text-on-surface/50">{opt.subtitle}</p>
              </div>
              {selected && (
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
                  check_circle
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Curator's Note */}
      <div className="mt-6 p-4 rounded-2xl bg-tertiary-fixed/50">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-on-tertiary-fixed-variant text-lg">lightbulb</span>
          <div>
            <p className="text-sm font-bold text-on-tertiary-fixed">Curator&apos;s Note</p>
            <p className="text-xs text-on-tertiary-fixed mt-1">
              Switching from daily beef to a plant-based diet can reduce your food-related emissions by up to 75%.
            </p>
          </div>
        </div>
      </div>

      <div className="mt-auto pt-6 flex items-center justify-between">
        <button onClick={() => navigate('/onboarding/commute')} className="text-on-surface/50 text-sm font-medium">
          Indietro
        </button>
        <button
          onClick={() => navigate('/onboarding/home')}
          className="bg-primary text-on-primary font-bold px-8 py-3 rounded-2xl active:scale-95 transition-all ease-out-expo flex items-center gap-2"
        >
          Prossimo <span className="material-symbols-outlined text-lg">arrow_forward</span>
        </button>
      </div>
    </div>
  )
}
