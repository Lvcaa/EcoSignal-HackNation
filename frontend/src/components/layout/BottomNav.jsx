import { NavLink } from 'react-router-dom'

const tabs = [
  { to: '/home', icon: 'home', label: 'Home' },
  { to: '/actions', icon: 'eco', label: 'Azioni' },
  { to: '/community', icon: 'groups', label: 'Community' },
  { to: '/progress', icon: 'bar_chart', label: 'Progress' },
  { to: '/profile', icon: 'person', label: 'Profilo' },
]

export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white/85 backdrop-blur-xl border-t border-outline-variant/30">
      <div className="max-w-md mx-auto flex justify-around py-2">
        {tabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-4 py-1.5 rounded-2xl transition-all duration-300 ease-out-expo ${
                isActive ? 'bg-primary-fixed/30 text-primary' : 'text-on-surface/50'
              }`
            }
          >
            <span className="material-symbols-outlined text-xl">{tab.icon}</span>
            <span className="text-[10px] font-medium">{tab.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
