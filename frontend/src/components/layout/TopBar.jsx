import { useAuthStore } from '../../store/auth'
import { useNotificationStore } from '../../store/notifications'
import NotificationPanel from '../ui/NotificationPanel'

export default function TopBar() {
  const displayName = useAuthStore((s) => s.display_name)
  const { unreadCount, togglePanel } = useNotificationStore()
  const initials = displayName
    ? displayName.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
    : '?'

  return (
    <>
      <header className="sticky top-0 z-50 bg-white/85 backdrop-blur-xl border-b border-outline-variant/30 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <img src="/green-buddy-logo.png" alt="Green Buddy" className="w-8 h-8 rounded-lg object-cover" />
          <span className="text-primary font-extrabold text-lg italic">Green Buddy</span>
        </div>
        <div className="flex items-center gap-3">
          <button className="relative" onClick={togglePanel}>
            <span className="material-symbols-outlined text-on-surface/60">notifications</span>
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>
        </div>
      </header>
      <NotificationPanel />
    </>
  )
}
