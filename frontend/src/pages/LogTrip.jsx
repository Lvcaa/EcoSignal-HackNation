import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogAction } from '../hooks/useDashboard'

const MODES = [
  { key: 'car', icon: 'directions_car', label: 'Auto', factor: 0.21 },
  { key: 'transit', icon: 'directions_bus', label: 'Mezzi', factor: 0.089 },
  { key: 'bike', icon: 'pedal_bike', label: 'Bici', factor: 0 },
  { key: 'walk', icon: 'directions_walk', label: 'A piedi', factor: 0 },
]

export default function LogTrip() {
  const navigate = useNavigate()
  const logAction = useLogAction()

  const [mode, setMode] = useState(null)
  const [distance, setDistance] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const selectedMode = MODES.find((m) => m.key === mode)
  const distanceKm = parseFloat(distance) || 0
  const co2Kg = selectedMode ? +(selectedMode.factor * distanceKm).toFixed(3) : 0

  const canSubmit = mode && distanceKm > 0

  const handleSubmit = async () => {
    if (!canSubmit) return
    setSaving(true)
    setError(null)

    try {
      await logAction.mutateAsync({
        action_type: 'trip',
        co2_delta_kg: co2Kg,
        description: `${selectedMode.label} - ${distanceKm} km`,
        metadata: { transport_mode: mode, distance_km: distanceKm },
      })
      navigate('/actions')
    } catch (err) {
      setError('Salvataggio non riuscito. Riprova.')
      setSaving(false)
    }
  }

  return (
    <div className="pb-4 px-4">
      {/* Header */}
      <div className="mt-4 flex items-center gap-3">
        <button onClick={() => navigate('/actions')} className="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center">
          <span className="material-symbols-outlined text-on-surface">arrow_back</span>
        </button>
        <h2 className="text-lg font-bold text-on-surface">Registra Viaggio</h2>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-2xl bg-red-50 border border-red-200">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Transport mode selector */}
      <div className="mt-6 bg-surface-container-lowest rounded-2xl shadow-card p-5">
        <p className="font-bold text-on-surface mb-4">Mezzo di trasporto</p>
        <div className="grid grid-cols-4 gap-2">
          {MODES.map((m) => (
            <button
              key={m.key}
              onClick={() => setMode(m.key)}
              className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${
                mode === m.key
                  ? 'bg-primary text-on-primary shadow-lg scale-105'
                  : 'bg-surface-container-high text-on-surface/60'
              }`}
            >
              <span className="material-symbols-outlined text-2xl">{m.icon}</span>
              <span className="text-[10px] font-bold">{m.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Distance input */}
      <div className="mt-4 bg-surface-container-lowest rounded-2xl shadow-card p-5">
        <p className="font-bold text-on-surface mb-3">Distanza</p>
        <div className="flex items-center gap-3">
          <input
            type="number"
            inputMode="decimal"
            min="0"
            step="0.1"
            value={distance}
            onChange={(e) => setDistance(e.target.value)}
            placeholder="0"
            className="flex-1 p-3 rounded-xl bg-surface-container-high text-2xl font-bold text-on-surface text-center placeholder:text-on-surface/20 focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <span className="text-lg font-bold text-on-surface/50">km</span>
        </div>
      </div>

      {/* CO2 preview */}
      {canSubmit && (
        <div className="mt-4 bg-surface-container-lowest rounded-2xl shadow-card p-5 text-center">
          <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-on-surface/40 mb-2">Emissioni stimate</p>
          <p className={`text-4xl font-black ${co2Kg === 0 ? 'text-primary' : 'text-on-surface'}`}>
            {co2Kg.toFixed(2)}
          </p>
          <p className="text-sm text-on-surface/50 mt-1">kg CO&#x2082;</p>
          {co2Kg === 0 && (
            <p className="text-xs text-primary font-medium mt-2">Zero emissioni! Ottima scelta!</p>
          )}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit || saving}
        className="mt-6 w-full py-3 rounded-2xl bg-primary text-on-primary font-bold text-sm disabled:opacity-40 transition-opacity"
      >
        {saving ? 'Salvataggio...' : 'Salva viaggio'}
      </button>
    </div>
  )
}
