import React from 'react';
import { Report } from '../types';
import { colors } from '../config/theme';

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  sent: { label: 'Inviata', color: '#FF9500' },
  in_progress: { label: 'In lavorazione', color: '#2196F3' },
  resolved: { label: 'Risolta', color: '#4CAF50' },
};

interface WebReportDetailProps {
  report: Report | null;
  onClose: () => void;
}

export default function WebReportDetail({ report, onClose }: WebReportDetailProps) {
  if (!report) return null;

  const statusCfg = STATUS_CONFIG[report.status] || STATUS_CONFIG.sent;
  const date = new Date(report.createdAt).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={{ ...styles.statusBadge, backgroundColor: statusCfg.color + '20' }}>
          <div style={{ ...styles.statusDot, backgroundColor: statusCfg.color }} />
          <span style={{ ...styles.statusText, color: statusCfg.color }}>
            {statusCfg.label}
          </span>
        </div>
        <button style={styles.closeButton} onClick={onClose}>
          ✕
        </button>
      </div>

      {/* Indirizzo */}
      <div style={styles.address}>{report.address}</div>

      {/* Foto */}
      {report.photo && (
        <img
          src={report.photo}
          alt="Segnalazione"
          style={styles.photo}
        />
      )}

      {/* Dettagli */}
      <div style={styles.details}>
        <DetailRow label="Data" value={date} />
        <DetailRow label="Cestino" value={report.binId} />
        <DetailRow label="Coordinate" value={`${report.lat.toFixed(4)}, ${report.lng.toFixed(4)}`} />
      </div>

      {/* XP */}
      <div style={styles.xpRow}>
        <span style={styles.xpIcon}>⚡</span>
        <span style={styles.xpText}>+{report.xp} XP</span>
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={styles.detailRow}>
      <span style={styles.detailLabel}>{label}</span>
      <span style={styles.detailValue}>{value}</span>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: 'absolute',
    bottom: 24,
    left: 24,
    width: 340,
    backgroundColor: colors.white,
    borderRadius: 16,
    padding: 20,
    boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
    zIndex: 1000,
    fontFamily: 'Inter, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  statusBadge: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 12,
    paddingRight: 12,
    paddingTop: 4,
    paddingBottom: 4,
    borderRadius: 999,
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontWeight: 600,
    fontSize: 14,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: 18,
    color: colors.textSecondary,
    cursor: 'pointer',
    padding: 4,
    lineHeight: 1,
  },
  address: {
    fontFamily: 'Manrope, -apple-system, sans-serif',
    fontWeight: 700,
    fontSize: 17,
    color: colors.textPrimary,
    marginBottom: 12,
  },
  photo: {
    width: '100%',
    height: 120,
    objectFit: 'cover' as const,
    borderRadius: 12,
    marginBottom: 12,
  },
  details: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  detailRow: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: 500,
    color: colors.textPrimary,
  },
  xpRow: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
  },
  xpIcon: {
    fontSize: 16,
  },
  xpText: {
    fontWeight: 600,
    fontSize: 15,
    color: '#FF9500',
  },
};
