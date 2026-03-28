import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/auth'
import { getProfile } from '../api/profile'

const transportLabels = {
  car: 'Auto',
  transit: 'Trasporto pubblico',
  bike: 'Bicicletta',
  walk: 'A piedi',
  mixed: 'Mix',
}

const dietLabels = {
  meat_daily: 'Carne ogni giorno',
  meat_weekly: 'Carne qualche volta',
  vegetarian: 'Vegetariano',
  vegan: 'Vegano',
}

export default function Profile() {
  const navigate = useNavigate()
  const { display_name, logout } = useAuthStore()
  const profile = useQuery({
    queryKey: ['profile'],
    queryFn: () => getProfile().then((r) => r.data),
  })

  const p = profile.data
  const initials = (display_name || p?.display_name || '?')
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const handleLogout = () => {
    logout()
    navigate('/welcome')
  }

  return (
    <div className="pb-4 px-4">
      {/* Avatar + name */}
      <div className="flex flex-col items-center mt-8 mb-6">
        <div className="w-20 h-20 rounded-full bg-primary flex items-center justify-center text-on-primary text-2xl font-black mb-3">
          {initials}
        </div>
        <h2 className="text-xl font-bold text-on-surface">{display_name || p?.display_name || 'User'}</h2>
        <p className="text-sm text-on-surface/50">{p?.email || ''}</p>
      </div>

      {/* Habits */}
      <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5 mb-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-on-surface">Le mie abitudini</h3>
          <button
            onClick={() => navigate('/onboarding/zip')}
            className="text-xs text-primary font-bold flex items-center gap-1"
          >
            <span className="material-symbols-outlined text-sm">edit</span>
            Modifica
          </button>
        </div>

        {profile.isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => <div key={i} className="skeleton h-6 w-full" />)}
          </div>
        ) : (
          <div className="space-y-4">
            <ProfileRow icon="location_on" label="CAP" value={p?.zip_code || '—'} />
            <ProfileRow icon="directions_bus" label="Trasporto" value={transportLabels[p?.transport_mode] || '—'} />
            <ProfileRow icon="restaurant" label="Dieta" value={dietLabels[p?.diet_type] || '—'} />
            <ProfileRow icon="home" label="Casa" value={p?.home_type ? `${p.home_type}, ${p.home_size_sqm}m²` : '—'} />
          </div>
        )}
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full py-3.5 rounded-2xl border-2 border-red-200 text-red-500 font-bold active:scale-95 transition-all ease-out-expo"
      >
        Esci
      </button>
    </div>
  )
}

function ProfileRow({ icon, label, value }) {
  return (
    <div className="flex items-center gap-3">
      <span className="material-symbols-outlined text-primary text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
        {icon}
      </span>
      <div className="flex-1">
        <p className="text-[10px] uppercase text-on-surface/40 font-bold tracking-wider">{label}</p>
        <p className="text-sm text-on-surface font-medium">{value}</p>
      </div>
    </div>
  )
}
