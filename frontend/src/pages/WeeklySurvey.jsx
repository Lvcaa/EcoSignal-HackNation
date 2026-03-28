import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSubmitSurvey } from '../hooks/useDashboard'

const TEMPS = [
  { value: 'cold', label: 'Freddo 30\u00b0', icon: 'ac_unit' },
  { value: 'warm', label: 'Tiepido 40\u00b0', icon: 'thermostat' },
  { value: 'hot', label: 'Caldo 60\u00b0', icon: 'local_fire_department' },
  { value: 'very_hot', label: 'Molto caldo 90\u00b0', icon: 'whatshot' },
]

const MODES = [
  { value: 'eco', label: 'Eco', icon: 'eco' },
  { value: 'normal', label: 'Normale', icon: 'water_drop' },
  { value: 'intensive', label: 'Intensivo', icon: 'bolt' },
]

function getWeekStart() {
  const now = new Date()
  const day = now.getDay()
  const diff = day === 0 ? 6 : day - 1
  const monday = new Date(now)
  monday.setDate(now.getDate() - diff)
  return monday.toISOString().slice(0, 10)
}

function CycleStepper({ value, onChange, label }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-on-surface/70">{label}</span>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => onChange(Math.max(0, value - 1))}
          className="w-9 h-9 rounded-full bg-surface-container-high flex items-center justify-center text-on-surface active:scale-95 transition-transform"
        >
          <span className="material-symbols-outlined text-lg">remove</span>
        </button>
        <span className="text-lg font-bold text-on-surface w-6 text-center">{value}</span>
        <button
          type="button"
          onClick={() => onChange(Math.min(14, value + 1))}
          className="w-9 h-9 rounded-full bg-surface-container-high flex items-center justify-center text-on-surface active:scale-95 transition-transform"
        >
          <span className="material-symbols-outlined text-lg">add</span>
        </button>
      </div>
    </div>
  )
}

function OptionSelector({ options, selected, onSelect }) {
  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onSelect(opt.value)}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
            selected === opt.value
              ? 'bg-primary text-on-primary'
              : 'bg-surface-container-high text-on-surface/60 hover:bg-surface-container-high/80'
          }`}
        >
          <span className="material-symbols-outlined text-base">{opt.icon}</span>
          {opt.label}
        </button>
      ))}
    </div>
  )
}

export default function WeeklySurvey() {
  const navigate = useNavigate()
  const submitSurvey = useSubmitSurvey()

  const [wmCycles, setWmCycles] = useState(3)
  const [wmTemp, setWmTemp] = useState('warm')
  const [dwCycles, setDwCycles] = useState(3)
  const [dwMode, setDwMode] = useState('normal')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    setError(null)
    try {
      const data = await submitSurvey.mutateAsync({
        washing_machine_cycles: wmCycles,
        washing_machine_temp: wmTemp,
        dishwasher_cycles: dwCycles,
        dishwasher_mode: dwMode,
        week_start: getWeekStart(),
      })
      setResult(data)
    } catch (err) {
      setError('Invio non riuscito. Riprova.')
    }
  }

  return (
    <div className="pb-4 px-4">
      {/* Header */}
      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={() => navigate('/home')}
          className="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center"
        >
          <span className="material-symbols-outlined text-on-surface">arrow_back</span>
        </button>
        <h2 className="text-lg font-bold text-on-surface">Questionario Settimanale</h2>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-2xl bg-red-50 border border-red-200">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {!result ? (
        <div className="mt-6 space-y-6">
          {/* Washing Machine */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">&#x1f9fa;</span>
              <h3 className="font-bold text-on-surface">Lavatrice</h3>
            </div>
            <CycleStepper
              value={wmCycles}
              onChange={setWmCycles}
              label="Cicli questa settimana"
            />
            <p className="text-xs text-on-surface/50 mt-4 mb-1">Temperatura prevalente</p>
            <OptionSelector options={TEMPS} selected={wmTemp} onSelect={setWmTemp} />
          </div>

          {/* Dishwasher */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">&#x1f37d;</span>
              <h3 className="font-bold text-on-surface">Lavastoviglie</h3>
            </div>
            <CycleStepper
              value={dwCycles}
              onChange={setDwCycles}
              label="Cicli questa settimana"
            />
            <p className="text-xs text-on-surface/50 mt-4 mb-1">Programma prevalente</p>
            <OptionSelector options={MODES} selected={dwMode} onSelect={setDwMode} />
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={submitSurvey.isPending}
            className="w-full py-3 rounded-2xl bg-primary text-on-primary font-bold text-sm disabled:opacity-40 transition-opacity"
          >
            {submitSurvey.isPending ? 'Invio in corso...' : 'Invia questionario'}
          </button>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {/* Result summary */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5 text-center">
            <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-on-surface/40 mb-2">
              Questa settimana
            </p>
            <p className="text-4xl font-black text-on-surface">
              {result.co2_breakdown.total_kg.toFixed(2)}
            </p>
            <p className="text-sm text-on-surface/50 mt-1">kg CO&#x2082; per gli elettrodomestici</p>
          </div>

          {/* Breakdown */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5">
            <p className="font-bold text-on-surface mb-3">Dettaglio</p>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-on-surface/70">&#x1f9fa; Lavatrice ({result.washing_machine_cycles} cicli)</span>
                <span className="font-medium text-on-surface">{result.co2_breakdown.washing_machine_kg.toFixed(2)} kg</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-on-surface/70">&#x1f37d; Lavastoviglie ({result.dishwasher_cycles} cicli)</span>
                <span className="font-medium text-on-surface">{result.co2_breakdown.dishwasher_kg.toFixed(2)} kg</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => navigate('/home')}
            className="w-full py-3 rounded-2xl bg-primary text-on-primary font-bold text-sm"
          >
            Torna alla home
          </button>
        </div>
      )}
    </div>
  )
}
