import React from 'react';
import { TruckState } from '../types';
import { wasteTypeColors, wasteTypeLabels, colors, fonts } from '../config/theme';

interface WebTruckDetailProps {
  truck: TruckState | null;
  onClose: () => void;
}

export default function WebTruckDetail({ truck, onClose }: WebTruckDetailProps) {
  if (!truck) return null;

  const wasteColor = wasteTypeColors[truck.waste_type];
  const timeStr = new Date(truck.position_timestamp).toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={{ ...styles.wasteTypeBadge, backgroundColor: wasteColor + '20' }}>
          <div style={{ ...styles.wasteTypeDot, backgroundColor: wasteColor }} />
          <span style={{ ...styles.wasteTypeText, color: wasteColor }}>
            {wasteTypeLabels[truck.waste_type]}
          </span>
        </div>
        <div style={styles.headerRight}>
          <span style={styles.truckId}>{truck.truck_id}</span>
          <button style={styles.closeButton} onClick={onClose}>
            ✕
          </button>
        </div>
      </div>

      {/* Dettagli */}
      <div style={styles.details}>
        <DetailRow label="Posizione" value={`${truck.latitude.toFixed(4)}, ${truck.longitude.toFixed(4)}`} />
        <DetailRow label="Ultimo aggiornamento" value={timeStr} />
        <DetailRow label="Versione dati" value={`v${truck.version}`} />
        {truck.company_id && <DetailRow label="Azienda" value={truck.company_id} />}
      </div>

      {/* Stato */}
      <div style={styles.statusRow}>
        <div style={{ ...styles.statusDot, backgroundColor: colors.success }} />
        <span style={styles.statusText}>In movimento</span>
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
    marginBottom: 16,
  },
  headerRight: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  wasteTypeBadge: {
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
  wasteTypeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  wasteTypeText: {
    fontWeight: 600,
    fontSize: 14,
  },
  truckId: {
    fontFamily: 'Manrope, -apple-system, sans-serif',
    fontWeight: 700,
    fontSize: 18,
    color: colors.textPrimary,
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
  statusRow: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 16,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontWeight: 500,
    fontSize: 14,
    color: colors.textPrimary,
  },
};
