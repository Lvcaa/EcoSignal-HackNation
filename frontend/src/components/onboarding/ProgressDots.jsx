export default function ProgressDots({ current, total = 6 }) {
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`h-1.5 rounded-full transition-all duration-500 ease-out-expo ${
            i < current
              ? 'w-8 bg-primary'
              : i === current
                ? 'w-8 bg-primary'
                : 'w-8 bg-outline-variant/40'
          }`}
        />
      ))}
    </div>
  )
}
