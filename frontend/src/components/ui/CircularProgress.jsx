export default function CircularProgress({
  value = 0,
  baselineValue,
  size = 192,
  strokeWidth = 12,
  colorClass,
  children,
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.min(100, Math.max(0, value)) / 100) * circumference

  // Baseline outer ring (slightly larger radius)
  const outerStroke = strokeWidth * 0.6
  const outerRadius = (size - outerStroke) / 2
  const outerCircumference = 2 * Math.PI * outerRadius
  const outerOffset =
    baselineValue != null
      ? outerCircumference - (Math.min(100, Math.max(0, baselineValue)) / 100) * outerCircumference
      : outerCircumference

  // Determine stroke color based on colorClass or gradient
  const strokeColor = colorClass === 'green'
    ? '#146940'
    : colorClass === 'orange'
      ? '#e67e22'
      : colorClass === 'red'
        ? '#dc2626'
        : undefined

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id="ring-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#146940" />
            <stop offset="100%" stopColor="#47a1ff" />
          </linearGradient>
        </defs>

        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e2e8f8"
          strokeWidth={strokeWidth}
        />

        {/* Baseline outer ring (if provided) */}
        {baselineValue != null && (
          <>
            <circle
              cx={size / 2}
              cy={size / 2}
              r={outerRadius}
              fill="none"
              stroke="#e2e8f8"
              strokeWidth={outerStroke}
              opacity={0.5}
            />
            <circle
              cx={size / 2}
              cy={size / 2}
              r={outerRadius}
              fill="none"
              stroke="#9ca3af"
              strokeWidth={outerStroke}
              strokeLinecap="round"
              strokeDasharray={outerCircumference}
              strokeDashoffset={outerOffset}
              opacity={0.4}
              className="transition-all duration-1000 ease-out-expo"
            />
          </>
        )}

        {/* Current value ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={strokeColor || 'url(#ring-gradient)'}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out-expo"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {children}
      </div>
    </div>
  )
}
