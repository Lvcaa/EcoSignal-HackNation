import { useState } from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import type { Report } from '../types';
import './ReportMarker.css';

const STATUS_COLORS: Record<string, string> = {
  sent: '#FF9500',
  in_progress: '#2196F3',
};

const STATUS_LABELS: Record<string, string> = {
  sent: 'Inviata',
  in_progress: 'In lavorazione',
};

function createReportIcon(status: string): L.DivIcon {
  const color = STATUS_COLORS[status] || '#FF9500';
  return L.divIcon({
    className: `report-marker ${status}`,
    html: `
      <div class="report-pin">
        <div class="report-pin-ring" style="border-color:${color};"></div>
        <div class="report-pin-body" style="background:${color};box-shadow:0 4px 14px ${color}55;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
            <rect x="11" y="4" width="2" height="10" rx="1"/>
            <rect x="11" y="17" width="2" height="3" rx="1"/>
          </svg>
        </div>
        <div class="report-pin-tail" style="border-top-color:${color};"></div>
      </div>
    `,
    iconSize: [36, 46],
    iconAnchor: [18, 46],
    popupAnchor: [0, -50],
  });
}

interface ReportMarkerProps {
  report: Report;
  onClick: () => void;
}

export default function ReportMarkerComponent({ report, onClick }: ReportMarkerProps) {
  const [status, setStatus] = useState(report.status);
  const [loading, setLoading] = useState(false);

  const icon = createReportIcon(status);
  const color = STATUS_COLORS[status] || '#FF9500';
  const dateStr = new Date(report.createdAt).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });

  async function handleTakeCharge() {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/reports/${report.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'in_progress' }),
      });
      if (res.ok) setStatus('in_progress');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Marker
      position={[report.lat, report.lng]}
      icon={icon}
      zIndexOffset={1000}
      eventHandlers={{ click: onClick }}
    >
      <Popup className="report-popup">
        <div className="report-popup-accent" style={{ background: color }} />
        <div className="report-popup-content">
          <div className="report-popup-header">
            <div className="report-popup-icon" style={{ background: color + '18', color }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <rect x="11" y="4" width="2" height="10" rx="1"/>
                <rect x="11" y="17" width="2" height="3" rx="1"/>
              </svg>
            </div>
            <span className="report-popup-badge" style={{ background: color + '18', color }}>
              {STATUS_LABELS[status]}
            </span>
          </div>
          <div className="report-popup-address">{report.address}</div>
          <div className="report-popup-meta">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
            </svg>
            {dateStr}
          </div>
          {status === 'sent' && (
            <button
              className="report-popup-take-charge"
              style={{ background: color }}
              onClick={handleTakeCharge}
              disabled={loading}
            >
              {loading ? 'Caricamento…' : 'Prendi in carico'}
            </button>
          )}
        </div>
      </Popup>
    </Marker>
  );
}
