import { useState } from 'react'
import { useCommunityStats, useJoinChallenge, useLeaderboard, useUserActions } from '../hooks/useCommunity'
import { useAirQuality } from '../hooks/useDashboard'
import { useAuthStore } from '../store/auth'
import { GoogleMap, useJsApiLoader, MarkerF, CircleF } from '@react-google-maps/api'
import ActionTimeline from '../components/ui/ActionTimeline'

export default function Community() {
  const stats = useCommunityStats()
  const joinChallenge = useJoinChallenge()
  const airQuality = useAirQuality()
  const zipCode = useAuthStore((s) => s.zip_code)
  const userId = useAuthStore((s) => s.user_id)
  const userLat = useAuthStore((s) => s.latitude)
  const userLng = useAuthStore((s) => s.longitude)
  const userAddress = useAuthStore((s) => s.address)

  const [leaderboardFilter, setLeaderboardFilter] = useState('all') // 'all' | 'neighborhood'
  const [selectedUser, setSelectedUser] = useState(null) // leaderboard entry or null
  const userActions = useUserActions(selectedUser?.user_id)
  const leaderboard = useLeaderboard(leaderboardFilter === 'neighborhood' ? zipCode : undefined)

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '',
  })

  const userPosition = userLat && userLng ? { lat: userLat, lng: userLng } : null

  const aqData = airQuality.data
  const aqLabel = aqData?.aqi_label || 'good'
  const AQ_COLORS = {
    good: { fill: '#146940', stroke: '#0d4a2c', label: 'Buona', bg: 'bg-primary' },
    moderate: { fill: '#d4a017', stroke: '#a07d12', label: 'Moderata', bg: 'bg-yellow-500' },
    unhealthy: { fill: '#e65100', stroke: '#bf4300', label: 'Non salubre', bg: 'bg-orange-600' },
    hazardous: { fill: '#b71c1c', stroke: '#8b1515', label: 'Pericolosa', bg: 'bg-red-700' },
  }
  const aqStyle = AQ_COLORS[aqLabel] || AQ_COLORS.good

  const neighborhood = stats.data?.neighborhood || stats.data
  const challenge = stats.data?.challenge

  const yourKg = neighborhood?.your_kg_co2_week ?? 0.8
  const avgKg = neighborhood?.avg_kg_co2_week ?? 1.2
  const betterPct = neighborhood?.better_than_pct ?? 35
  const city = neighborhood?.city || 'Your City'
  const participants = neighborhood?.participant_count ?? 312

  const entries = leaderboard.data?.entries || []
  const userRankIdx = entries.findIndex((e) => e.user_id === userId)

  const getInitials = (name) => {
    const parts = name.split(' ')
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    return name.slice(0, 2).toUpperCase()
  }

  const MEDAL_COLORS = [
    'bg-yellow-400 text-yellow-900', // gold
    'bg-gray-300 text-gray-700',     // silver
    'bg-amber-600 text-amber-100',   // bronze
  ]

  return (
    <div className="pb-4 px-4">
      {/* Header */}
      <div className="mt-4 mb-6">
        <div className="flex items-center gap-2 text-xs text-on-surface/50 font-medium uppercase tracking-wider">
          <span className="material-symbols-outlined text-primary text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
            location_on
          </span>
          {city}
        </div>
        <h1 className="text-2xl font-black text-on-surface mt-1">Your Neighborhood</h1>
        <div className="flex items-center gap-2 mt-1">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          <span className="text-xs text-on-surface/50">{participants} Green Buddies near you</span>
        </div>
      </div>

      {/* Carbon Comparison */}
      <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5 mb-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-bold text-on-surface">Carbon Comparison</h3>
            <p className="text-xs text-on-surface/50">Your footprint vs. neighbors</p>
          </div>
          <span className="material-symbols-outlined text-on-surface/30">compare_arrows</span>
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-xs font-bold mb-1.5">
              <span className="text-on-surface/60">YOU</span>
              <span>{yourKg.toFixed(1)} KG CO2</span>
            </div>
            <div className="h-2.5 bg-surface-container-high rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-1000 ease-out-expo"
                style={{ width: `${(yourKg / Math.max(yourKg, avgKg)) * 100}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs font-bold mb-1.5">
              <span className="text-on-surface/60">NEIGHBORHOOD AVG</span>
              <span>{avgKg.toFixed(1)} KG CO2</span>
            </div>
            <div className="h-2.5 bg-surface-container-high rounded-full overflow-hidden">
              <div
                className="h-full bg-secondary rounded-full transition-all duration-1000 ease-out-expo"
                style={{ width: `${(avgKg / Math.max(yourKg, avgKg)) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {betterPct > 0 && (
          <p className="text-sm text-primary italic mt-4 font-medium">
            You are doing {betterPct.toFixed(0)}% better than the local average this week!
          </p>
        )}
      </div>

      {/* Leaderboard */}
      <div className="bg-surface-container-lowest rounded-2xl shadow-card mb-4 overflow-hidden">
        <div className="flex items-center justify-between px-5 pt-4 pb-2">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
              emoji_events
            </span>
            <h3 className="font-bold text-on-surface">Leaderboard</h3>
          </div>
          <span className="text-[10px] font-bold text-primary bg-primary-fixed/30 px-2 py-0.5 rounded-full uppercase">
            Weekly
          </span>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 px-5 pb-3">
          <button
            onClick={() => setLeaderboardFilter('all')}
            className={`text-xs font-bold px-3 py-1 rounded-full transition-all ${
              leaderboardFilter === 'all'
                ? 'bg-primary text-on-primary'
                : 'bg-surface-container-high text-on-surface/60'
            }`}
          >
            All Users
          </button>
          <button
            onClick={() => setLeaderboardFilter('neighborhood')}
            className={`text-xs font-bold px-3 py-1 rounded-full transition-all ${
              leaderboardFilter === 'neighborhood'
                ? 'bg-primary text-on-primary'
                : 'bg-surface-container-high text-on-surface/60'
            }`}
          >
            My Area
          </button>
        </div>

        {/* Leaderboard list */}
        {leaderboard.isLoading ? (
          <div className="px-5 pb-5">
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-surface-container-high rounded-xl animate-pulse" />
              ))}
            </div>
          </div>
        ) : entries.length === 0 ? (
          <div className="px-5 pb-5 text-center">
            <span className="material-symbols-outlined text-on-surface/20 text-3xl">group</span>
            <p className="text-xs text-on-surface/40 mt-1">No leaderboard data yet</p>
          </div>
        ) : (
          <div className="px-3 pb-3">
            {/* Top 3 podium */}
            {entries.length >= 3 && (
              <div className="flex items-end justify-center gap-2 mb-4 pt-2">
                {/* 2nd place */}
                <button onClick={() => setSelectedUser(entries[1])} className="flex flex-col items-center w-1/3 active:scale-95 transition-transform">
                  <div className={`w-11 h-11 rounded-full ${MEDAL_COLORS[1]} flex items-center justify-center text-xs font-black`}>
                    {getInitials(entries[1].display_name)}
                  </div>
                  <p className="text-[10px] font-bold text-on-surface mt-1 text-center truncate w-full">{entries[1].display_name.split(' ')[0]}</p>
                  <p className="text-[10px] text-on-surface/50">{entries[1].kg_co2_week} kg</p>
                  <div className="w-full bg-gray-200 rounded-t-lg mt-1 h-12 flex items-center justify-center">
                    <span className="text-sm font-black text-gray-500">2</span>
                  </div>
                </button>
                {/* 1st place */}
                <button onClick={() => setSelectedUser(entries[0])} className="flex flex-col items-center w-1/3 active:scale-95 transition-transform">
                  <span className="material-symbols-outlined text-yellow-500 text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                    emoji_events
                  </span>
                  <div className={`w-13 h-13 rounded-full ${MEDAL_COLORS[0]} flex items-center justify-center text-sm font-black ring-2 ring-yellow-300`}>
                    {getInitials(entries[0].display_name)}
                  </div>
                  <p className="text-[10px] font-bold text-on-surface mt-1 text-center truncate w-full">{entries[0].display_name.split(' ')[0]}</p>
                  <p className="text-[10px] text-primary font-bold">{entries[0].kg_co2_week} kg</p>
                  <div className="w-full bg-primary/20 rounded-t-lg mt-1 h-16 flex items-center justify-center">
                    <span className="text-sm font-black text-primary">1</span>
                  </div>
                </button>
                {/* 3rd place */}
                <button onClick={() => setSelectedUser(entries[2])} className="flex flex-col items-center w-1/3 active:scale-95 transition-transform">
                  <div className={`w-11 h-11 rounded-full ${MEDAL_COLORS[2]} flex items-center justify-center text-xs font-black`}>
                    {getInitials(entries[2].display_name)}
                  </div>
                  <p className="text-[10px] font-bold text-on-surface mt-1 text-center truncate w-full">{entries[2].display_name.split(' ')[0]}</p>
                  <p className="text-[10px] text-on-surface/50">{entries[2].kg_co2_week} kg</p>
                  <div className="w-full bg-amber-100 rounded-t-lg mt-1 h-8 flex items-center justify-center">
                    <span className="text-sm font-black text-amber-700">3</span>
                  </div>
                </button>
              </div>
            )}

            {/* Rest of leaderboard */}
            <div className="space-y-1">
              {entries.slice(entries.length >= 3 ? 3 : 0, 20).map((entry) => {
                const isUser = entry.user_id === userId
                return (
                  <button
                    key={entry.user_id}
                    onClick={() => setSelectedUser(entry)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all w-full text-left active:scale-[0.98] ${
                      isUser
                        ? 'bg-primary-fixed/40 ring-1 ring-primary/30'
                        : 'hover:bg-surface-container-low'
                    }`}
                  >
                    <span className="w-6 text-xs font-bold text-on-surface/40 text-right shrink-0">
                      {entry.rank}
                    </span>
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                        isUser
                          ? 'bg-primary text-on-primary'
                          : 'bg-secondary-fixed text-secondary'
                      }`}
                    >
                      {getInitials(entry.display_name)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm truncate ${isUser ? 'font-bold text-primary' : 'font-medium text-on-surface'}`}>
                        {entry.display_name}
                        {isUser && <span className="text-[10px] ml-1 opacity-60">(you)</span>}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className={`text-xs font-bold ${isUser ? 'text-primary' : 'text-on-surface'}`}>
                        {entry.kg_co2_week} kg
                      </p>
                      <p className="text-[9px] text-on-surface/40">CO2/week</p>
                    </div>
                  </button>
                )
              })}
            </div>

            {/* Your position if not in top 20 */}
            {userRankIdx >= 20 && (
              <>
                <div className="flex items-center justify-center py-2">
                  <span className="text-on-surface/20 text-xs">...</span>
                </div>
                <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-primary-fixed/40 ring-1 ring-primary/30">
                  <span className="w-6 text-xs font-bold text-primary text-right shrink-0">
                    {entries[userRankIdx].rank}
                  </span>
                  <div className="w-8 h-8 rounded-full bg-primary text-on-primary flex items-center justify-center text-[10px] font-bold shrink-0">
                    {getInitials(entries[userRankIdx].display_name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-primary truncate">
                      {entries[userRankIdx].display_name}
                      <span className="text-[10px] ml-1 opacity-60">(you)</span>
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs font-bold text-primary">{entries[userRankIdx].kg_co2_week} kg</p>
                    <p className="text-[9px] text-on-surface/40">CO2/week</p>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Air Quality Map */}
      <div className="bg-surface-container-lowest rounded-2xl shadow-card overflow-hidden mb-4">
        <div className="flex items-center justify-between px-5 pt-4 pb-2">
          <h3 className="font-bold text-on-surface">Air Quality Map</h3>
          <span className="text-[10px] font-bold text-primary bg-primary-fixed/30 px-2 py-0.5 rounded-full uppercase">
            Live
          </span>
        </div>

        {/* Air quality stats bar */}
        {aqData && (
          <div className="flex items-center gap-3 px-5 pb-3">
            <span className={`w-2.5 h-2.5 rounded-full ${aqStyle.bg}`} />
            <span className="text-xs font-semibold text-on-surface">{aqStyle.label}</span>
            {aqData.pm25 != null && (
              <span className="text-[10px] text-on-surface/50">PM2.5: {aqData.pm25.toFixed(1)}</span>
            )}
            {aqData.pm10 != null && (
              <span className="text-[10px] text-on-surface/50">PM10: {aqData.pm10.toFixed(1)}</span>
            )}
          </div>
        )}

        {/* Google Map */}
        <div className="h-52 relative">
          {isLoaded && userPosition ? (
            <GoogleMap
              mapContainerStyle={{ width: '100%', height: '100%' }}
              center={userPosition}
              zoom={14}
              options={{
                disableDefaultUI: true,
                zoomControl: true,
                mapTypeControl: false,
                streetViewControl: false,
                styles: [
                  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
                  { featureType: 'transit', stylers: [{ visibility: 'off' }] },
                ],
              }}
            >
              {/* Air quality radius circle */}
              <CircleF
                center={userPosition}
                radius={800}
                options={{
                  fillColor: aqStyle.fill,
                  fillOpacity: 0.15,
                  strokeColor: aqStyle.stroke,
                  strokeOpacity: 0.4,
                  strokeWeight: 2,
                }}
              />
              {/* User location marker */}
              <MarkerF
                position={userPosition}
                title={userAddress || 'La tua posizione'}
              />
            </GoogleMap>
          ) : isLoaded ? (
            <div className="h-full flex items-center justify-center bg-surface-container-low">
              <div className="text-center">
                <span className="material-symbols-outlined text-on-surface/30 text-3xl">location_off</span>
                <p className="text-xs text-on-surface/40 mt-1">Inserisci il tuo indirizzo nel profilo</p>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center bg-surface-container-low">
              <span className="text-xs text-on-surface/40">Caricamento mappa...</span>
            </div>
          )}
        </div>
      </div>

      {/* Weekly Challenge */}
      <div className="bg-primary rounded-2xl p-5 mb-4 text-on-primary">
        <p className="text-[10px] uppercase tracking-[0.2em] font-bold opacity-80 flex items-center gap-1">
          <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
          Weekly Challenge
        </p>
        <h3 className="text-xl font-black mt-1">{challenge?.title || 'No car on Wednesday'}</h3>
        <div className="flex items-center justify-between text-xs mt-3 opacity-80">
          <span>{challenge?.progress_pct?.toFixed(0) || 47}% of neighborhood joined</span>
          <span>{challenge?.participant_count || 912}/{challenge?.participant_target || 2000}</span>
        </div>
        <div className="h-1.5 bg-white/20 rounded-full mt-2 overflow-hidden">
          <div
            className="h-full bg-white rounded-full"
            style={{ width: `${challenge?.progress_pct || 47}%` }}
          />
        </div>
        <button
          onClick={() => joinChallenge.mutate()}
          disabled={joinChallenge.isPending || challenge?.user_joined}
          className="w-full mt-4 bg-white text-primary font-bold py-3 rounded-2xl active:scale-95 transition-all ease-out-expo disabled:opacity-50"
        >
          {challenge?.user_joined ? 'Already joined!' : 'Join the challenge'}
        </button>
      </div>

      {/* AI Curator Insight */}
      <div className="bg-surface-container-lowest rounded-2xl shadow-card p-5 mb-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-secondary/10 flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-secondary text-lg">auto_awesome</span>
          </div>
          <div>
            <p className="font-bold text-sm text-on-surface">Curator Insight</p>
            <p className="text-xs text-on-surface/60 mt-1">
              Traffic patterns suggest that taking the <span className="font-bold">Subway Line 4</span> today
              will reduce your community&apos;s cumulative emissions by 14kg.
            </p>
          </div>
        </div>
      </div>

      {/* User Profile Bottom Sheet */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-end justify-center" onClick={() => setSelectedUser(null)}>
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          <div
            className="relative w-full max-w-lg bg-surface-container-lowest rounded-t-3xl shadow-2xl animate-slide-up max-h-[85vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drag handle */}
            <div className="flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-on-surface/20" />
            </div>

            {/* Close button */}
            <button
              onClick={() => setSelectedUser(null)}
              className="absolute top-3 right-4 w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center"
            >
              <span className="material-symbols-outlined text-on-surface/60 text-lg">close</span>
            </button>

            {/* Profile header */}
            <div className="flex flex-col items-center px-5 pt-4 pb-5">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center text-lg font-black ${
                selectedUser.user_id === userId
                  ? 'bg-primary text-on-primary'
                  : selectedUser.rank <= 3
                    ? MEDAL_COLORS[selectedUser.rank - 1]
                    : 'bg-secondary-fixed text-secondary'
              }`}>
                {getInitials(selectedUser.display_name)}
              </div>
              <h2 className="text-xl font-black text-on-surface mt-3">{selectedUser.display_name}</h2>
              {selectedUser.user_id === userId && (
                <span className="text-xs text-primary font-medium mt-0.5">(you)</span>
              )}
              <div className="flex items-center gap-1.5 mt-1">
                <span className="material-symbols-outlined text-on-surface/40 text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                  location_on
                </span>
                <span className="text-xs text-on-surface/50">{selectedUser.zip_code}</span>
              </div>
            </div>

            {/* Stats row */}
            <div className="flex justify-center gap-6 px-5 pb-5">
              <div className="flex flex-col items-center bg-surface-container-high rounded-2xl px-5 py-3 min-w-[90px]">
                <span className="material-symbols-outlined text-primary text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                  emoji_events
                </span>
                <span className="text-xl font-black text-on-surface mt-1">#{selectedUser.rank}</span>
                <span className="text-[10px] text-on-surface/50 uppercase font-bold tracking-wider">Rank</span>
              </div>
              <div className="flex flex-col items-center bg-surface-container-high rounded-2xl px-5 py-3 min-w-[90px]">
                <span className="material-symbols-outlined text-primary text-xl">eco</span>
                <span className="text-xl font-black text-on-surface mt-1">{selectedUser.kg_co2_week}</span>
                <span className="text-[10px] text-on-surface/50 uppercase font-bold tracking-wider">kg CO2/wk</span>
              </div>
              {avgKg > 0 && (
                <div className="flex flex-col items-center bg-surface-container-high rounded-2xl px-5 py-3 min-w-[90px]">
                  <span className="material-symbols-outlined text-xl" style={{
                    color: selectedUser.kg_co2_week <= avgKg ? '#146940' : '#e65100'
                  }}>
                    {selectedUser.kg_co2_week <= avgKg ? 'trending_down' : 'trending_up'}
                  </span>
                  <span className="text-xl font-black text-on-surface mt-1">
                    {Math.abs(((selectedUser.kg_co2_week - avgKg) / avgKg) * 100).toFixed(0)}%
                  </span>
                  <span className="text-[10px] text-on-surface/50 uppercase font-bold tracking-wider">
                    {selectedUser.kg_co2_week <= avgKg ? 'Below avg' : 'Above avg'}
                  </span>
                </div>
              )}
            </div>

            {/* CO2 bar comparison vs avg */}
            <div className="px-5 pb-5">
              <div className="bg-surface-container-high rounded-2xl p-4">
                <p className="text-xs font-bold text-on-surface/50 uppercase tracking-wider mb-3">vs. Neighborhood Average</p>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1">
                      <span className="text-on-surface/60">{selectedUser.display_name.split(' ')[0]}</span>
                      <span>{selectedUser.kg_co2_week} kg</span>
                    </div>
                    <div className="h-2.5 bg-surface-container-lowest rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          selectedUser.kg_co2_week <= avgKg ? 'bg-primary' : 'bg-orange-500'
                        }`}
                        style={{ width: `${Math.min((selectedUser.kg_co2_week / Math.max(selectedUser.kg_co2_week, avgKg)) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1">
                      <span className="text-on-surface/60">Neighborhood Avg</span>
                      <span>{avgKg.toFixed(1)} kg</span>
                    </div>
                    <div className="h-2.5 bg-surface-container-lowest rounded-full overflow-hidden">
                      <div
                        className="h-full bg-secondary rounded-full transition-all duration-700"
                        style={{ width: `${Math.min((avgKg / Math.max(selectedUser.kg_co2_week, avgKg)) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Today's Actions */}
            <div className="px-5 pb-24">
              <h3 className="font-bold text-on-surface mb-3 flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-lg">history</span>
                Today&apos;s Actions
              </h3>
              <ActionTimeline
                actions={Array.isArray(userActions.data) ? userActions.data : userActions.data?.actions ?? []}
                isLoading={userActions.isLoading}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
