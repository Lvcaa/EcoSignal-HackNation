import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogAction } from '../hooks/useDashboard'
import { analyzeImage } from '../api/imageAnalyzer'

const STEPS = { INPUT: 'input', ANALYZING: 'analyzing', RESULT: 'result', SAVING: 'saving' }

export default function LogClothing() {
  const navigate = useNavigate()
  const logAction = useLogAction()

  const [step, setStep] = useState(STEPS.INPUT)
  const [description, setDescription] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)

  const handlePhoto = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    setStep(STEPS.ANALYZING)
    setError(null)

    try {
      const base64 = await fileToBase64(file)
      const res = await analyzeImage(base64, 'clothing', description || undefined)
      setAnalysis(res.data)
      setStep(STEPS.RESULT)
    } catch (err) {
      setError('Analisi non riuscita. Riprova.')
      setStep(STEPS.INPUT)
    }
  }

  const handleTextSubmit = async () => {
    if (!description.trim()) return
    setStep(STEPS.ANALYZING)
    setError(null)

    try {
      const res = await analyzeImage(null, 'clothing', description)
      setAnalysis(res.data)
      setStep(STEPS.RESULT)
    } catch (err) {
      setError('Analisi non riuscita. Riprova.')
      setStep(STEPS.INPUT)
    }
  }

  const handleSave = async () => {
    setStep(STEPS.SAVING)
    try {
      await logAction.mutateAsync({
        action_type: 'clothing',
        co2_delta_kg: analysis?.co2_estimate_kg ?? 0,
        description: analysis?.summary || description,
        image_analysis_id: analysis?.id || null,
        metadata: { items: analysis?.items || [] },
      })
      navigate('/actions')
    } catch (err) {
      setError('Salvataggio non riuscito. Riprova.')
      setStep(STEPS.RESULT)
    }
  }

  return (
    <div className="pb-4 px-4">
      {/* Header */}
      <div className="mt-4 flex items-center gap-3">
        <button onClick={() => navigate('/actions')} className="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center">
          <span className="material-symbols-outlined text-on-surface">arrow_back</span>
        </button>
        <h2 className="text-lg font-bold text-on-surface">Registra Vestiti</h2>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-2xl bg-red-50 border border-red-200">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {step === STEPS.INPUT && (
        <div className="mt-6 space-y-6">
          {/* Camera capture */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5">
            <p className="font-bold text-on-surface mb-3">Scatta una foto</p>
            <label className="flex flex-col items-center gap-3 p-6 border-2 border-dashed border-outline-variant/40 rounded-2xl cursor-pointer hover:bg-surface-container-high/30 transition-colors">
              <span className="material-symbols-outlined text-4xl text-primary">checkroom</span>
              <span className="text-sm text-on-surface/60">Fotografa il capo di abbigliamento</span>
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handlePhoto}
                className="hidden"
              />
            </label>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-outline-variant/30" />
            <span className="text-xs text-on-surface/40 font-medium">oppure</span>
            <div className="flex-1 h-px bg-outline-variant/30" />
          </div>

          {/* Text description */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5">
            <p className="font-bold text-on-surface mb-3">Descrivi il capo</p>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Es: Maglietta in cotone biologico comprata al mercatino dell'usato"
              className="w-full h-24 p-3 rounded-xl bg-surface-container-high text-sm text-on-surface placeholder:text-on-surface/30 resize-none focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
            <button
              onClick={handleTextSubmit}
              disabled={!description.trim()}
              className="mt-3 w-full py-3 rounded-2xl bg-primary text-on-primary font-bold text-sm disabled:opacity-40 transition-opacity"
            >
              Analizza
            </button>
          </div>
        </div>
      )}

      {step === STEPS.ANALYZING && (
        <div className="mt-12 flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-primary-fixed/30 flex items-center justify-center animate-pulse">
            <span className="material-symbols-outlined text-primary text-3xl">checkroom</span>
          </div>
          <p className="text-sm font-medium text-on-surface/60">Analisi in corso...</p>
        </div>
      )}

      {step === STEPS.RESULT && analysis && (
        <div className="mt-6 space-y-4">
          <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5 text-center">
            <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-on-surface/40 mb-2">Impatto stimato</p>
            <p className="text-4xl font-black text-on-surface">
              {(analysis.co2_estimate_kg ?? 0).toFixed(2)}
            </p>
            <p className="text-sm text-on-surface/50 mt-1">kg CO&#x2082;</p>
          </div>

          {analysis.summary && (
            <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5">
              <p className="font-bold text-on-surface mb-2">Riepilogo</p>
              <p className="text-sm text-on-surface/70">{analysis.summary}</p>
            </div>
          )}

          {analysis.items?.length > 0 && (
            <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5">
              <p className="font-bold text-on-surface mb-2">Capi rilevati</p>
              <ul className="space-y-1">
                {analysis.items.map((item, i) => (
                  <li key={i} className="text-sm text-on-surface/70 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                    {item.name || item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={handleSave}
            className="w-full py-3 rounded-2xl bg-primary text-on-primary font-bold text-sm"
          >
            Salva azione
          </button>
        </div>
      )}

      {step === STEPS.SAVING && (
        <div className="mt-12 flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-primary-fixed/30 flex items-center justify-center animate-pulse">
            <span className="material-symbols-outlined text-primary text-3xl">save</span>
          </div>
          <p className="text-sm font-medium text-on-surface/60">Salvataggio...</p>
        </div>
      )}
    </div>
  )
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
