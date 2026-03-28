import { useNavigate } from 'react-router-dom'

export default function Welcome() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-surface max-w-md mx-auto flex flex-col relative overflow-hidden">
      {/* Decorative blurred circles */}
      <div className="absolute -top-20 -right-20 w-60 h-60 bg-primary-fixed/20 rounded-full blur-3xl" />
      <div className="absolute -bottom-20 -left-20 w-60 h-60 bg-secondary-fixed/20 rounded-full blur-3xl" />

      <header className="flex items-center justify-between px-5 py-4 relative z-10">
        <div className="flex items-center gap-2">
          <img src="/green-buddy-logo.png" alt="Green Buddy" className="w-7 h-7 rounded-lg object-cover" />
          <span className="text-primary font-extrabold text-lg italic">Green Buddy</span>
        </div>
        <button onClick={() => navigate('/login')} className="text-on-surface/50">
          <span className="material-symbols-outlined">close</span>
        </button>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center px-6 relative z-10">
        {/* Mascot logo */}
        <img src="/green-buddy-logo.png" alt="Green Buddy" className="w-28 h-28 rounded-3xl object-cover mb-8 shadow-card-lg" />

        <h1 className="text-4xl font-black text-primary text-center leading-tight mb-3">
          Green Buddy
        </h1>
        <p className="text-on-surface/60 text-center text-sm mb-10">
          Il tuo compagno per un futuro sostenibile
        </p>

        {/* Let's Talk card */}
        <button
          onClick={() => navigate('/onboarding/zip')}
          className="w-full bg-surface-container-lowest rounded-3xl p-5 shadow-card border-2 border-primary-fixed/40 text-left mb-4 active:scale-95 transition-transform ease-out-expo"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="w-10 h-10 bg-primary-fixed/30 rounded-xl flex items-center justify-center">
              <span className="material-symbols-outlined text-primary">chat_bubble</span>
            </div>
            <span className="bg-primary text-on-primary text-[10px] font-bold uppercase px-3 py-1 rounded-full tracking-wider">
              Consigliato
            </span>
          </div>
          <p className="font-bold text-lg text-on-surface">Parliamo</p>
          <p className="text-xs text-on-surface/50 mt-1">
            Un percorso conversazionale per capire le tue abitudini quotidiane attraverso il dialogo.
          </p>
        </button>

        {/* Quick Setup card */}
        <button
          onClick={() => navigate('/onboarding/zip')}
          className="w-full bg-surface-container-lowest rounded-3xl p-5 shadow-card border border-outline-variant/30 text-left mb-6 active:scale-95 transition-transform ease-out-expo"
        >
          <div className="w-10 h-10 bg-secondary-fixed/30 rounded-xl flex items-center justify-center mb-3">
            <span className="material-symbols-outlined text-secondary">bolt</span>
          </div>
          <p className="font-bold text-lg text-on-surface">Setup Rapido</p>
          <p className="text-xs text-on-surface/50 mt-1">
            Un wizard passo-passo per chi conosce già i propri numeri.
          </p>
        </button>

        <button
          onClick={() => navigate('/login')}
          className="text-secondary text-sm font-medium"
        >
          Esplora prima
        </button>
      </div>
    </div>
  )
}
