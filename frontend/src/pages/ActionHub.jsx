import { useNavigate } from 'react-router-dom'
import { useDailyActions } from '../hooks/useDashboard'

const today = () => new Date().toISOString().slice(0, 10)

const categories = [
  { key: 'meal', emoji: '\uD83C\uDF7D\uFE0F', label: 'Pasto', path: '/actions/meal', color: 'from-orange-400 to-amber-300' },
  { key: 'trip', emoji: '\uD83D\uDE97', label: 'Viaggio', path: '/actions/trip', color: 'from-blue-400 to-cyan-300' },
  { key: 'grocery', emoji: '\uD83D\uDED2', label: 'Spesa', path: '/actions/grocery', color: 'from-green-400 to-emerald-300' },
  { key: 'clothing', emoji: '\uD83D\uDC55', label: 'Vestiti', path: '/actions/clothing', color: 'from-purple-400 to-fuchsia-300' },
]

export default function ActionHub() {
  const navigate = useNavigate()
  const daily = useDailyActions(today())

  const actionCount = daily.data?.actions?.length ?? 0
  const totalCo2 = daily.data?.total_co2_delta_kg ?? 0

  return (
    <div className="pb-4 px-4">
      {/* Today summary */}
      <div className="mt-4 bg-gradient-to-br from-primary to-primary-container rounded-3xl p-6 text-on-primary text-center">
        <p className="text-[10px] uppercase tracking-[0.2em] font-bold bg-white/20 inline-block px-3 py-1 rounded-full mb-3">
          Le tue azioni di oggi
        </p>
        <div className="flex items-center justify-center gap-6">
          <div>
            <p className="text-4xl font-black">{actionCount}</p>
            <p className="text-xs opacity-80 mt-1">azioni</p>
          </div>
          <div className="w-px h-12 bg-white/30" />
          <div>
            <p className="text-4xl font-black">{Math.abs(totalCo2).toFixed(1)}</p>
            <p className="text-xs opacity-80 mt-1">kg CO&#x2082; {totalCo2 <= 0 ? 'risparmiati' : 'emessi'}</p>
          </div>
        </div>
      </div>

      {/* Category cards */}
      <h3 className="font-bold text-on-surface mt-6 mb-3">Registra un'azione</h3>
      <div className="grid grid-cols-2 gap-3">
        {categories.map((cat) => (
          <button
            key={cat.key}
            onClick={() => navigate(cat.path)}
            className="bg-surface-container-lowest rounded-2xl shadow-card p-5 flex flex-col items-center gap-3 active:scale-95 transition-transform"
          >
            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${cat.color} flex items-center justify-center`}>
              <span className="text-2xl">{cat.emoji}</span>
            </div>
            <span className="font-bold text-sm text-on-surface">{cat.label}</span>
          </button>
        ))}
      </div>

      {/* Recent actions */}
      {actionCount > 0 && (
        <div className="mt-6">
          <h3 className="font-bold text-on-surface mb-3">Azioni recenti</h3>
          <div className="space-y-2">
            {daily.data.actions.slice(0, 5).map((action) => (
              <div
                key={action.id}
                className="bg-surface-container-lowest rounded-2xl shadow-card p-4 flex items-center gap-3"
              >
                <span className="text-xl">
                  {action.action_type === 'meal' ? '\uD83C\uDF7D\uFE0F' :
                   action.action_type === 'trip' ? '\uD83D\uDE97' :
                   action.action_type === 'grocery' ? '\uD83D\uDED2' : '\uD83D\uDC55'}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-on-surface truncate">
                    {action.description || action.action_type}
                  </p>
                  <p className="text-xs text-on-surface/50">
                    {new Date(action.created_at).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <span className={`text-sm font-bold ${action.co2_delta_kg <= 0 ? 'text-primary' : 'text-error'}`}>
                  {action.co2_delta_kg <= 0 ? '' : '+'}{action.co2_delta_kg.toFixed(2)} kg
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
