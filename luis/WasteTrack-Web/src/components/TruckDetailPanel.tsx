import type { TruckState } from '../types';
import { wasteTypeColors, wasteTypeLabels } from '../config/theme';
import './TruckDetailPanel.css';

interface TruckDetailPanelProps {
  truck: TruckState | null;
  onClose: () => void;
}

export default function TruckDetailPanel({ truck, onClose }: TruckDetailPanelProps) {
  if (!truck) return null;

  const wasteColor = wasteTypeColors[truck.waste_type];
  const timeStr = new Date(truck.position_timestamp).toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return (
    <div className="detail-panel">
      <button className="detail-close" onClick={onClose}>✕</button>

      <div className="detail-header">
        <span className="waste-badge" style={{ backgroundColor: wasteColor + '20', color: wasteColor }}>
          <span className="waste-dot" style={{ backgroundColor: wasteColor }} />
          {wasteTypeLabels[truck.waste_type]}
        </span>
        <span className="truck-id">{truck.truck_id}</span>
      </div>

      <div className="detail-rows">
        <div className="detail-row">
          <span className="detail-label">Posizione</span>
          <span className="detail-value">{truck.latitude.toFixed(4)}, {truck.longitude.toFixed(4)}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Ultimo aggiornamento</span>
          <span className="detail-value">{timeStr}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Versione dati</span>
          <span className="detail-value">v{truck.version}</span>
        </div>
        {truck.company_id && (
          <div className="detail-row">
            <span className="detail-label">Azienda</span>
            <span className="detail-value">{truck.company_id}</span>
          </div>
        )}
      </div>

      <div className="detail-status">
        <span className="status-dot" />
        In movimento
      </div>
    </div>
  );
}
