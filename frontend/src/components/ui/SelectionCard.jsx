export default function SelectionCard({ icon, title, subtitle, selected, onClick, className = '' }) {
  return (
    <button
      onClick={onClick}
      className={`relative w-full text-left p-4 rounded-2xl border-2 transition-all duration-300 ease-out-expo active:scale-95 ${
        selected
          ? 'bg-primary-container border-primary text-on-primary shadow-card-lg'
          : 'bg-surface-container-lowest border-outline-variant/30 hover:border-primary/30 shadow-card'
      } ${className}`}
    >
      {selected && (
        <span className="absolute top-3 right-3 w-2.5 h-2.5 bg-primary-fixed rounded-full" />
      )}
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${
        selected ? 'bg-white/20' : 'bg-primary-fixed/20'
      }`}>
        <span className={`material-symbols-outlined ${selected ? 'text-on-primary' : 'text-primary'}`}>
          {icon}
        </span>
      </div>
      <p className={`font-bold text-sm ${selected ? 'text-on-primary' : 'text-on-surface'}`}>{title}</p>
      <p className={`text-xs mt-0.5 ${selected ? 'text-on-primary/70' : 'text-on-surface/50'}`}>{subtitle}</p>
    </button>
  )
}
