import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/auth'
import { getProfile } from '../api/profile'
import { impersonate, listUsers } from '../api/auth'
import { getLeaderboard } from '../api/community'

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
  const queryClient = useQueryClient()
  const { display_name, user_id: currentUserId, original_auth, logout, setZip, setLocation, startImpersonation, stopImpersonation } = useAuthStore()
  const [switching, setSwitching] = useState(null) // user_id being switched to
  const [switchError, setSwitchError] = useState(null)
  const [showAllUsers, setShowAllUsers] = useState(false)
  const isImpersonating = !!original_auth
  const profile = useQuery({
    queryKey: ['profile'],
    queryFn: () => getProfile().then((r) => r.data),
  })
  const allUsers = useQuery({
    queryKey: ['all-users'],
    queryFn: () => listUsers(200).then((r) => r.data),
  })
  const leaderboard = useQuery({
    queryKey: ['leaderboard-all'],
    queryFn: () => getLeaderboard().then((r) => r.data),
  })

  // Merge: leaderboard users first (ranked), then remaining users
  const leaderboardEntries = leaderboard.data?.entries || []
  const rankedIds = new Set(leaderboardEntries.map((e) => e.user_id))
  const unrankedUsers = (allUsers.data || [])
    .filter((u) => !rankedIds.has(u.user_id))
    .map((u) => ({ ...u, rank: null, kg_co2_week: null }))
  const users = [
    ...leaderboardEntries,
    ...unrankedUsers,
  ]

  const handleSwitchUser = async (entry) => {
    // If clicking the current impersonated user, revert to original
    if (entry.user_id === currentUserId && isImpersonating) {
      stopImpersonation()
      queryClient.invalidateQueries()
      return
    }
    setSwitching(entry.user_id)
    setSwitchError(null)
    try {
      const res = await impersonate(entry.user_id)
      const { access_token, user_id, display_name: name } = res.data
      startImpersonation(access_token, user_id || entry.user_id, name || entry.display_name)
      // Fetch new user's profile to update zip/location
      const profileRes = await getProfile()
      const p = profileRes.data
      if (p.zip_code) setZip(p.zip_code)
      if (p.address) setLocation(p.address, p.latitude, p.longitude)
      // Clear all cached queries so they refetch with new token
      queryClient.invalidateQueries()
    } catch (err) {
      setSwitchError(err.response?.data?.detail || 'Failed to switch user')
    } finally {
      setSwitching(null)
    }
  }

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

      {/* Demo User Switcher */}
      <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="material-symbols-outlined text-secondary text-lg">swap_horiz</span>
          <h3 className="font-bold text-on-surface">Switch User</h3>
          <span className="text-[10px] font-bold text-secondary bg-secondary/10 px-2 py-0.5 rounded-full uppercase ml-auto">
            Pitch
          </span>
        </div>
        <p className="text-xs text-on-surface/50 mb-3">
          {isImpersonating
            ? 'Tap the active user to switch back to your account.'
            : 'Switch to any user account for the demo.'}
        </p>

        {isImpersonating && (
          <button
            onClick={() => { stopImpersonation(); queryClient.invalidateQueries() }}
            className="flex items-center gap-2 w-full mb-3 px-3 py-2.5 rounded-xl bg-amber-50 ring-1 ring-amber-300 active:scale-[0.98] transition-all"
          >
            <span className="material-symbols-outlined text-amber-600 text-lg">undo</span>
            <span className="text-sm font-bold text-amber-700">Back to {original_auth.display_name}</span>
            <span className="material-symbols-outlined text-amber-400 text-lg ml-auto">arrow_back</span>
          </button>
        )}

        {allUsers.isLoading && leaderboard.isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <div key={i} className="skeleton h-12 w-full rounded-xl" />)}
          </div>
        ) : (
          <div className="space-y-1.5">
            {(showAllUsers ? users : users.slice(0, 5)).map((entry) => {
              const isCurrent = entry.user_id === currentUserId
              const isSwitching = switching === entry.user_id
              const nameInitials = entry.display_name
                .split(' ')
                .map((w) => w[0])
                .join('')
                .toUpperCase()
                .slice(0, 2)
              return (
                <button
                  key={entry.user_id}
                  onClick={() => handleSwitchUser(entry)}
                  disabled={!!switching || (isCurrent && !isImpersonating)}
                  className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl transition-all active:scale-[0.98] ${
                    isCurrent
                      ? 'bg-primary-fixed/40 ring-1 ring-primary/30'
                      : 'bg-surface-container-high hover:bg-surface-container-highest'
                  } disabled:opacity-60`}
                >
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                    isCurrent ? 'bg-primary text-on-primary' : 'bg-secondary-fixed text-secondary'
                  }`}>
                    {nameInitials}
                  </div>
                  <div className="flex-1 text-left min-w-0">
                    <p className={`text-sm font-medium truncate ${isCurrent ? 'text-primary font-bold' : 'text-on-surface'}`}>
                      {entry.display_name}
                      {isCurrent && <span className="text-[10px] ml-1 opacity-60">(current)</span>}
                    </p>
                    <p className="text-[10px] text-on-surface/40 truncate">
                      {entry.rank ? `#${entry.rank} · ${entry.kg_co2_week} kg CO2/week` : entry.email || entry.zip_code || ''}
                    </p>
                  </div>
                  {isSwitching ? (
                    <div className="w-5 h-5 border-2 border-secondary border-t-transparent rounded-full animate-spin shrink-0" />
                  ) : isCurrent && isImpersonating ? (
                    <span className="material-symbols-outlined text-amber-500 text-lg shrink-0">close</span>
                  ) : isCurrent ? (
                    <span className="material-symbols-outlined text-primary text-lg shrink-0" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                  ) : (
                    <span className="material-symbols-outlined text-on-surface/30 text-lg shrink-0">arrow_forward</span>
                  )}
                </button>
              )
            })}
            {users.length > 5 && (
              <button
                onClick={() => setShowAllUsers(!showAllUsers)}
                className="w-full py-2 text-xs font-bold text-primary"
              >
                {showAllUsers ? 'Show less' : `Show all ${users.length} users`}
              </button>
            )}
          </div>
        )}

        {switchError && (
          <p className="text-xs text-red-500 mt-3 bg-red-50 rounded-lg px-3 py-2">{switchError}</p>
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
