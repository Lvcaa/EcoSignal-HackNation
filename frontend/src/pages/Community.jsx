import { useCommunityStats, useJoinChallenge } from '../hooks/useCommunity'
import { useAuthStore } from '../store/auth'

export default function Community() {
  const stats = useCommunityStats()
  const joinChallenge = useJoinChallenge()
  const zipCode = useAuthStore((s) => s.zip_code)

  const neighborhood = stats.data?.neighborhood || stats.data
  const challenge = stats.data?.challenge

  const yourKg = neighborhood?.your_kg_co2_week ?? 0.8
  const avgKg = neighborhood?.avg_kg_co2_week ?? 1.2
  const betterPct = neighborhood?.better_than_pct ?? 35
  const city = neighborhood?.city || 'Your City'
  const participants = neighborhood?.participant_count ?? 312

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

      {/* Air Quality Map */}
      <div className="bg-surface-container-lowest rounded-2xl shadow-card overflow-hidden mb-4">
        <div className="flex items-center justify-between px-5 pt-4">
          <h3 className="font-bold text-on-surface">Air Quality Map</h3>
          <span className="text-[10px] font-bold text-primary bg-primary-fixed/30 px-2 py-0.5 rounded-full uppercase">
            Live
          </span>
        </div>
        <div className="h-40 relative mt-2 bg-gradient-to-br from-primary/10 via-primary/5 to-secondary/10 flex items-end p-4">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(20,105,64,0.15),transparent_70%)]" />
          <div className="flex items-center gap-2 relative z-10">
            <span className="w-2.5 h-2.5 bg-primary rounded-full" />
            <span className="text-xs font-medium text-on-surface">Good Quality</span>
          </div>
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

      {/* Community Updates */}
      <h3 className="font-bold text-on-surface mt-6 mb-3">Community Updates</h3>
      <div className="space-y-3">
        <div className="flex items-start gap-3 bg-surface-container-lowest rounded-2xl p-4 shadow-card">
          <div className="w-9 h-9 rounded-full bg-primary-fixed flex items-center justify-center text-xs font-bold text-primary shrink-0">
            SM
          </div>
          <div>
            <p className="text-sm text-on-surface">
              <span className="font-bold">Sarah M.</span> just completed the &ldquo;Zero Waste Weekend&rdquo; challenge!
            </p>
            <p className="text-[11px] text-on-surface/40 mt-0.5">2 hours ago &middot; <span className="text-primary font-medium">+50 pts</span></p>
          </div>
        </div>
        <div className="flex items-start gap-3 bg-surface-container-lowest rounded-2xl p-4 shadow-card">
          <div className="w-9 h-9 rounded-full bg-secondary-fixed flex items-center justify-center text-xs font-bold text-secondary shrink-0">
            ML
          </div>
          <div>
            <p className="text-sm text-on-surface">
              <span className="font-bold">Marcus L.</span> shared a new shortcut for the bike lane on 5th Ave.
            </p>
            <p className="text-[11px] text-on-surface/40 mt-0.5">5 hours ago &middot; <span className="font-medium">12 helpful</span></p>
          </div>
        </div>
      </div>
    </div>
  )
}
