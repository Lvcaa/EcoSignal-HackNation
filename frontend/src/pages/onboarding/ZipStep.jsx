import { useState } from 'react'
import { useNavigate, useOutletContext } from 'react-router-dom'
import ProgressDots from '../../components/onboarding/ProgressDots'

const ZIP_MAP = {
  '00100': { city: 'Roma', region: 'Lazio' },
  '20100': { city: 'Milano', region: 'Lombardia' },
  '25100': { city: 'Brescia', region: 'Lombardia' },
  '24100': { city: 'Bergamo', region: 'Lombardia' },
  '80100': { city: 'Napoli', region: 'Campania' },
  '84100': { city: 'Salerno', region: 'Campania' },
  '90100': { city: 'Palermo', region: 'Sicilia' },
  '95100': { city: 'Catania', region: 'Sicilia' },
  '30100': { city: 'Venezia', region: 'Veneto' },
  '37100': { city: 'Verona', region: 'Veneto' },
  '35100': { city: 'Padova', region: 'Veneto' },
  '10100': { city: 'Torino', region: 'Piemonte' },
  '40100': { city: 'Bologna', region: 'Emilia-Romagna' },
  '43100': { city: 'Parma', region: 'Emilia-Romagna' },
  '70100': { city: 'Bari', region: 'Puglia' },
  '50100': { city: 'Firenze', region: 'Toscana' },
  '56100': { city: 'Pisa', region: 'Toscana' },
  '88100': { city: 'Catanzaro', region: 'Calabria' },
  '89100': { city: 'Reggio Calabria', region: 'Calabria' },
  '09100': { city: 'Cagliari', region: 'Sardegna' },
  '16100': { city: 'Genova', region: 'Liguria' },
  '60100': { city: 'Ancona', region: 'Marche' },
  '67100': { city: "L'Aquila", region: 'Abruzzo' },
  '65100': { city: 'Pescara', region: 'Abruzzo' },
  '38100': { city: 'Trento', region: 'Trentino-Alto Adige' },
  '39100': { city: 'Bolzano', region: 'Trentino-Alto Adige' },
  '34100': { city: 'Trieste', region: 'Friuli Venezia Giulia' },
  '06100': { city: 'Perugia', region: 'Umbria' },
  '85100': { city: 'Potenza', region: 'Basilicata' },
  '86100': { city: 'Campobasso', region: 'Molise' },
  '11100': { city: 'Aosta', region: "Valle d'Aosta" },
}

export default function ZipStep() {
  const navigate = useNavigate()
  const { data, updateData } = useOutletContext()
  const [zip, setZip] = useState(data.zip_code)
  const match = ZIP_MAP[zip]

  return (
    <div className="flex flex-col h-full">
      <ProgressDots current={0} total={6} />

      {/* Hero card */}
      <div className="relative rounded-3xl overflow-hidden mb-6 h-40">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/90 to-primary-container/90" />
        <div className="relative z-10 p-5 flex flex-col justify-end h-full text-on-primary">
          <p className="text-xs uppercase tracking-widest font-semibold opacity-80">Cominciamo</p>
          <h2 className="text-xl font-bold mt-1">Personalizza la tua esperienza ambientale</h2>
        </div>
      </div>

      <h3 className="text-lg font-black text-on-surface mb-1">Dove vivi?</h3>
      <p className="text-xs text-on-surface/50 mb-4">
        Il tuo CAP ci aiuta a mappare la qualit&agrave; dell&apos;aria e le iniziative green nel tuo quartiere.
      </p>

      <label className="text-[10px] font-bold text-on-surface/50 uppercase tracking-wider mb-1.5">
        Codice Postale (CAP)
      </label>
      <input
        type="text"
        inputMode="numeric"
        maxLength={5}
        value={zip}
        onChange={(e) => setZip(e.target.value.replace(/\D/g, '').slice(0, 5))}
        placeholder="es. 20121"
        className="w-full px-4 py-3.5 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-lg font-medium tracking-wider"
      />

      {match && (
        <div className="flex items-center gap-3 mt-3 p-3 rounded-2xl bg-surface-container-low">
          <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
            location_on
          </span>
          <div className="flex-1">
            <p className="text-sm font-semibold text-on-surface">{match.city}, {match.region}</p>
          </div>
          <button
            onClick={() => updateData({ zip_code: zip })}
            className="text-primary text-sm font-bold"
          >
            Conferma
          </button>
        </div>
      )}

      <div className="mt-auto pt-6 flex items-center justify-between">
        <button onClick={() => navigate('/welcome')} className="text-on-surface/50 text-sm font-medium">
          Salta
        </button>
        <button
          onClick={() => {
            updateData({ zip_code: zip })
            navigate('/onboarding/transport')
          }}
          disabled={!zip || zip.length < 5}
          className="bg-primary text-on-primary font-bold px-8 py-3 rounded-2xl active:scale-95 transition-all ease-out-expo disabled:opacity-40 flex items-center gap-2"
        >
          Prossimo <span className="material-symbols-outlined text-lg">arrow_forward</span>
        </button>
      </div>
    </div>
  )
}
