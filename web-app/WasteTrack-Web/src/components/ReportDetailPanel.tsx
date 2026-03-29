import type { Report } from '../types';
import './ReportDetailPanel.css';

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  sent: { label: 'Inviata', color: '#FF9500' },
  in_progress: { label: 'In lavorazione', color: '#2196F3' },
};

interface ReportDetailPanelProps {
  report: Report | null;
  onClose: () => void;
}

export default function ReportDetailPanel({ report, onClose }: ReportDetailPanelProps) {
  if (!report) return null;

  const cfg = STATUS_CONFIG[report.status] || STATUS_CONFIG.sent;
  const dateStr = new Date(report.createdAt).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="report-panel">
      <button className="detail-close" onClick={onClose}>✕</button>

      <div className="report-panel-header">
        <span className="report-status-badge" style={{ background: cfg.color + '20', color: cfg.color }}>
          <span className="report-status-dot" style={{ background: cfg.color }} />
          {cfg.label}
        </span>
      </div>

      <div className="report-panel-address">{report.address}</div>

      {report.photo && (
        <img className="report-panel-photo" src={report.photo} alt="Segnalazione" />
      )}

      <div className="detail-rows">
        <div className="detail-row">
          <span className="detail-label">Data</span>
          <span className="detail-value">{dateStr}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Cestino</span>
          <span className="detail-value">{report.binId}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Coordinate</span>
          <span className="detail-value">{report.lat.toFixed(4)}, {report.lng.toFixed(4)}</span>
        </div>
      </div>

      <div className="report-panel-xp">
        ⚡ +{report.xp} XP
      </div>
    </div>
  );
}
