import { useEffect, useRef, useState } from 'react';
import type { Report } from '../types';
import type { MapBounds } from '../hooks/useTrucks';
import './ReportEdgeIndicators.css';

interface Indicator {
  report: Report;
  x: number;
  y: number;
  angle: number;
}

interface Props {
  newReports: Report[];
  mapBounds: MapBounds | null;
  containerRef: React.RefObject<HTMLDivElement | null>;
  onFlyTo: (report: Report) => void;
}

const STATUS_COLORS: Record<string, string> = {
  sent: '#FF9500',
  in_progress: '#2196F3',
};

export default function ReportEdgeIndicators({ newReports, mapBounds, containerRef, onFlyTo }: Props) {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [containerSize, setContainerSize] = useState({ w: 0, h: 0 });
  const prevBoundsRef = useRef<MapBounds | null>(null);

  // Osserva dimensioni container
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => {
      setContainerSize({ w: el.clientWidth, h: el.clientHeight });
    });
    obs.observe(el);
    setContainerSize({ w: el.clientWidth, h: el.clientHeight });
    return () => obs.disconnect();
  }, [containerRef]);

  // Ricalcola indicatori quando cambiano report, bounds o dimensioni
  useEffect(() => {
    if (!mapBounds || containerSize.w === 0) return;

    const { north, south, east, west } = mapBounds;
    const { w, h } = containerSize;
    // Rettangolo di clipping asimmetrico (più spazio in alto per i filter pills)
    const mTop = 80, mBottom = 56, mLeft = 56, mRight = 56;
    // Centro del rettangolo di clipping
    const cx = (mLeft + w - mRight) / 2;
    const cy = (mTop + h - mBottom) / 2;
    const hw = (w - mLeft - mRight) / 2;
    const hh = (h - mTop - mBottom) / 2;

    const next: Indicator[] = [];

    for (const report of newReports) {
      const inBounds =
        report.lat >= south &&
        report.lat <= north &&
        report.lng >= west &&
        report.lng <= east;

      if (inBounds) continue;

      // Proiezione lat/lng → pixel (approssimata, buona per area locale)
      const px = ((report.lng - west) / (east - west)) * w;
      const py = ((north - report.lat) / (north - south)) * h;

      const dx = px - cx;
      const dy = py - cy;

      if (dx === 0 && dy === 0) continue;

      // Intersezione con il rettangolo dei bordi
      const scale =
        Math.abs(dx) * hh > Math.abs(dy) * hw
          ? hw / Math.abs(dx)
          : hh / Math.abs(dy);

      const ex = cx + dx * scale;
      const ey = cy + dy * scale;
      const angle = Math.atan2(dy, dx) * (180 / Math.PI);

      next.push({ report, x: ex, y: ey, angle });
    }

    setIndicators(next);
    prevBoundsRef.current = mapBounds;
  }, [newReports, mapBounds, containerSize]);

  return (
    <>
      {indicators.map(({ report, x, y, angle }) => {
        const color = STATUS_COLORS[report.status] ?? '#FF9500';
        return (
          <div
            key={report.id}
            className="edge-indicator"
            style={{
              left: x,
              top: y,
              '--indicator-color': color,
            } as React.CSSProperties}
            onClick={() => onFlyTo(report)}
            title={report.address}
          >
            {/* La freccia SVG punta verso l'alto a 0°; angle usa 0°=destra → +90° di offset */}
            <div className="edge-indicator-arrow" style={{ transform: `rotate(${angle + 90}deg)` }}>
              <svg width="12" height="16" viewBox="0 0 12 16" fill="white">
                <path d="M6 0L12 16H0L6 0Z" />
              </svg>
            </div>
          </div>
        );
      })}
    </>
  );
}
