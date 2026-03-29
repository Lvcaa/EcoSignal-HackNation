import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { chatOnboarding } from '../../api/chat'
import { submitOnboarding } from '../../api/profile'
import { calculateFootprint } from '../../api/footprint'
import { useOnboardingStore } from '../../store/onboarding'
import { useAuthStore } from '../../store/auth'

export default function ChatOnboarding() {
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)
  const setZip = useAuthStore((s) => s.setZip)
  const setLocation = useAuthStore((s) => s.setLocation)

  const {
    chatMessages,
    setChatMessages,
    addChatMessage,
    data: onboardingData,
    updateData,
  } = useOnboardingStore()

  const [input, setInput] = useState('')
  const [complete, setComplete] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)
  const [loading, setLoading] = useState(false)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [chatMessages])

  // Start conversation on mount — clear previous chat and begin fresh
  useEffect(() => {
    let cancelled = false
    setChatMessages([])
    setLoading(true)
    chatOnboarding([]).then(({ data: result }) => {
      if (cancelled) return
      setChatMessages([{ role: 'assistant', content: result.message }])
      if (result.extracted_data) {
        const cleaned = {}
        for (const [k, v] of Object.entries(result.extracted_data)) {
          if (v !== null && v !== undefined) cleaned[k] = v
        }
        if (Object.keys(cleaned).length > 0) updateData(cleaned)
      }
      setLoading(false)
    }).catch(() => {
      if (!cancelled) setLoading(false)
    })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Send message to Regolo
  const chatMutation = useMutation({
    mutationFn: async (messages) => {
      const currentData = useOnboardingStore.getState().data
      const { data } = await chatOnboarding(messages, currentData)
      return data
    },
    onSuccess: (result) => {
      addChatMessage({ role: 'assistant', content: result.message })

      if (result.extracted_data) {
        const cleaned = {}
        for (const [k, v] of Object.entries(result.extracted_data)) {
          if (v !== null && v !== undefined) cleaned[k] = v
        }
        if (Object.keys(cleaned).length > 0) updateData(cleaned)
      }

      if (result.complete) setComplete(true)
    },
  })

  const handleSend = () => {
    const text = input.trim()
    if (!text || chatMutation.isPending) return

    const userMsg = { role: 'user', content: text }
    addChatMessage(userMsg)
    setInput('')

    const apiMessages = [...chatMessages, userMsg].map(({ role, content }) => ({ role, content }))
    chatMutation.mutate(apiMessages)

    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Submit onboarding data
  const handleFinish = async () => {
    if (!token) {
      // Not logged in — go register, data is persisted in store
      navigate('/register')
      return
    }

    setSubmitting(true)
    try {
      const d = onboardingData
      await submitOnboarding({
        zip_code: d.zip_code,
        address: d.address || null,
        latitude: d.latitude,
        longitude: d.longitude,
        transport_mode: d.transport_mode,
        commute_days_per_week: d.commute_days_per_week ?? 5,
        diet_type: d.diet_type,
        home_type: d.home_type || 'apartment',
        home_size_sqm: d.home_size_sqm,
        has_pets: d.has_pets ?? false,
        pet_type: d.pet_type,
        pet_count: d.pet_count,
      })
      await calculateFootprint()
      setZip(d.zip_code)
      if (d.address) setLocation(d.address, d.latitude, d.longitude)
      useOnboardingStore.getState().clear()
      navigate('/home')
    } catch {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface max-w-md mx-auto flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-outline-variant/20">
        <button onClick={() => navigate('/welcome')} className="text-on-surface/60">
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <div className="flex items-center gap-2">
          <img src="/green-buddy-logo.png" alt="" className="w-6 h-6 rounded-lg object-cover" />
          <span className="text-primary font-extrabold text-lg italic">Parliamo</span>
        </div>
        <div className="w-6" />
      </header>

      {/* Chat area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {chatMessages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <img
                src="/green-buddy-logo.png"
                alt=""
                className="w-7 h-7 rounded-full object-cover mr-2 mt-1 flex-shrink-0"
              />
            )}
            <div
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary text-on-primary rounded-br-md'
                  : 'bg-surface-container-low text-on-surface rounded-bl-md'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {(chatMutation.isPending || loading) && (
          <div className="flex justify-start">
            <img
              src="/green-buddy-logo.png"
              alt=""
              className="w-7 h-7 rounded-full object-cover mr-2 mt-1 flex-shrink-0"
            />
            <div className="bg-surface-container-low text-on-surface/50 px-4 py-3 rounded-2xl rounded-bl-md text-sm">
              <span className="inline-flex gap-1">
                <span className="w-1.5 h-1.5 bg-on-surface/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-on-surface/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-on-surface/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            </div>
          </div>
        )}

        {chatMutation.error && (
          <div className="text-center text-xs text-red-500 py-2">
            Errore di connessione. Riprova.
          </div>
        )}
      </div>

      {/* Complete banner */}
      {complete && (
        <div className="px-4 py-3 bg-primary-fixed/20 border-t border-primary-fixed/30">
          <p className="text-sm font-semibold text-on-surface mb-2">
            Profilo completato!
          </p>
          <button
            onClick={handleFinish}
            disabled={submitting}
            className="w-full bg-primary text-on-primary font-bold py-3 rounded-2xl active:scale-95 transition-all ease-out-expo disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {submitting ? 'Calcolo in corso...' : (
              <>
                {token ? 'Scopri la tua impronta' : 'Registrati e scopri'}
                <span className="material-symbols-outlined text-lg">arrow_forward</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Input bar */}
      {!complete && (
        <div className="px-4 py-3 border-t border-outline-variant/20 bg-surface">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Scrivi un messaggio..."
              rows={1}
              className="flex-1 px-4 py-3 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-sm resize-none max-h-24"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || chatMutation.isPending}
              className="w-11 h-11 bg-primary text-on-primary rounded-full flex items-center justify-center active:scale-90 transition-all disabled:opacity-40"
            >
              <span className="material-symbols-outlined text-lg">send</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
