import { useNavigate } from 'react-router-dom'
import { useNotificationStore } from '../../store/notifications'

const TYPE_COLORS = {
  meal: 'bg-green-100 text-green-700',
  summary: 'bg-blue-100 text-blue-700',
  tip: 'bg-amber-100 text-amber-700',
}

export default function NotificationPanel() {
  const navigate = useNavigate()
  const { notifications, panelOpen, closePanel, markRead, markAllRead } = useNotificationStore()

  if (!panelOpen) return null

  const handleClick = (notif) => {
    markRead(notif.id)
    closePanel()
    navigate(notif.url)
  }

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-[60] bg-black/20" onClick={closePanel} />

      {/* Panel */}
      <div className="fixed top-14 right-2 left-2 z-[70] max-w-md mx-auto animate-in">
        <div className="bg-white rounded-2xl shadow-xl border border-outline-variant/20 overflow-hidden max-h-[70vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-outline-variant/20">
            <h3 className="text-sm font-bold text-on-surface">Notifiche giornaliere</h3>
            {notifications.some((n) => !n.read) && (
              <button
                onClick={markAllRead}
                className="text-xs text-primary font-semibold"
              >
                Segna tutte come lette
              </button>
            )}
          </div>

          {/* Info banner */}
          <div className="px-4 py-2.5 bg-primary-fixed/10 border-b border-outline-variant/10">
            <p className="text-[11px] text-on-surface/60 leading-relaxed">
              Ogni giorno riceverai queste notifiche per registrare i pasti e tenere traccia della tua giornata.
            </p>
          </div>

          {/* Notification list */}
          <div className="overflow-y-auto flex-1">
            {notifications.length === 0 ? (
              <div className="py-8 text-center">
                <span className="material-symbols-outlined text-3xl text-on-surface/20">notifications_off</span>
                <p className="text-sm text-on-surface/40 mt-2">Nessuna notifica</p>
              </div>
            ) : (
              <ul className="divide-y divide-outline-variant/10">
                {notifications.map((notif) => (
                  <li
                    key={notif.id}
                    onClick={() => handleClick(notif)}
                    className={`flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-surface-container-high/30 ${
                      !notif.read ? 'bg-primary-fixed/5' : ''
                    }`}
                  >
                    {/* Icon */}
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${TYPE_COLORS[notif.type] || 'bg-gray-100 text-gray-600'}`}>
                      <span className="material-symbols-outlined text-lg">{notif.icon}</span>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-on-surface">{notif.title}</span>
                        <span className="text-[10px] font-mono text-on-surface/40 bg-surface-container-high/50 px-1.5 py-0.5 rounded">
                          {notif.time}
                        </span>
                      </div>
                      <p className="text-xs text-on-surface/60 mt-0.5 leading-relaxed">{notif.body}</p>
                    </div>

                    {/* Unread dot */}
                    {!notif.read && (
                      <div className="w-2 h-2 rounded-full bg-primary shrink-0 mt-2" />
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
