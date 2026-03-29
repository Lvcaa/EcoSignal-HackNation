import React, { useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { TruckState, WasteType, Report } from '../types';
import { wasteTypeColors, colors } from '../config/theme';
import { ROMA_REGION } from '../config/theme';

// Colori stato segnalazione
const REPORT_STATUS_COLORS: Record<string, string> = {
  sent: '#FF9500',
  in_progress: '#2196F3',
};

// CSS per animazioni marker — iniettato una volta sola
const MARKER_CSS = `
  .truck-marker-icon {
    transition: transform 1s linear !important;
  }
  .truck-marker-icon.selected {
    z-index: 1000 !important;
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3));
  }
  .report-marker-icon {
    z-index: 500 !important;
  }
  .report-marker-icon.sent {
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.15); opacity: 0.85; }
  }
  .report-popup .leaflet-popup-content-wrapper {
    border-radius: 12px;
    padding: 0;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  }
  .report-popup .leaflet-popup-content {
    margin: 0;
    min-width: 200px;
  }
`;

let cssInjected = false;
function injectCSS() {
  if (cssInjected) return;
  const style = document.createElement('style');
  style.textContent = MARKER_CSS;
  document.head.appendChild(style);
  cssInjected = true;
}

// SVG inline per l'icona camion
function truckSVG(color: string, isSelected: boolean): string {
  const size = isSelected ? 48 : 40;
  const iconSize = isSelected ? 28 : 24;
  const borderRadius = 12;
  const bgColor = color + '33';

  return `
    <div style="
      width: ${size}px; height: ${size}px;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      ${isSelected ? 'transform: scale(1.15);' : ''}
    ">
      <div style="
        border-radius: ${borderRadius}px;
        border: 2px solid ${color};
        background: ${bgColor};
        padding: 4px;
        display: flex; align-items: center; justify-content: center;
      ">
        <svg width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" fill="none">
          <rect x="1" y="6" width="15" height="10" rx="2" fill="${color}"/>
          <path d="M16 9h3l3 4v3h-6V9z" fill="${color}" opacity="0.8"/>
          <circle cx="6" cy="17.5" r="1.5" fill="#1C1C1E"/>
          <circle cx="18" cy="17.5" r="1.5" fill="#1C1C1E"/>
          <rect x="3" y="8" width="5" height="3" rx="0.5" fill="white" opacity="0.9"/>
        </svg>
      </div>
      <div style="
        width: 6px; height: 6px;
        border-radius: 3px;
        background: ${color};
        margin-top: 2px;
      "></div>
    </div>
  `;
}

// Crea un DivIcon Leaflet per il camion
function createTruckIcon(wasteType: WasteType, isSelected: boolean): L.DivIcon {
  const color = wasteTypeColors[wasteType];
  const size = isSelected ? 48 : 40;
  return L.divIcon({
    className: `truck-marker-icon${isSelected ? ' selected' : ''}`,
    html: truckSVG(color, isSelected),
    iconSize: [size, size + 8],
    iconAnchor: [size / 2, (size + 8) / 2],
  });
}

// Marker singolo con animazione fluida
function AnimatedMarker({ truck, isSelected, onSelect }: {
  truck: TruckState;
  isSelected: boolean;
  onSelect: (truck: TruckState) => void;
}) {
  const markerRef = useRef<L.Marker>(null);
  const icon = createTruckIcon(truck.waste_type, isSelected);

  // Quando la posizione cambia, setLatLng attiva il CSS transition
  useEffect(() => {
    if (markerRef.current) {
      markerRef.current.setLatLng([truck.latitude, truck.longitude]);
    }
  }, [truck.latitude, truck.longitude]);

  // Aggiorna icona quando cambia selezione
  useEffect(() => {
    if (markerRef.current) {
      markerRef.current.setIcon(icon);
    }
  }, [isSelected]);

  return (
    <Marker
      ref={markerRef}
      position={[truck.latitude, truck.longitude]}
      icon={icon}
      eventHandlers={{
        click: () => onSelect(truck),
      }}
    />
  );
}

// Componente interno per tracciare i bounds della mappa
function BoundsTracker({ onBoundsChange }: {
  onBoundsChange: (bounds: { northEast: { latitude: number; longitude: number }; southWest: { latitude: number; longitude: number } }) => void;
}) {
  const map = useMapEvents({
    moveend: () => {
      const b = map.getBounds();
      onBoundsChange({
        northEast: { latitude: b.getNorthEast().lat, longitude: b.getNorthEast().lng },
        southWest: { latitude: b.getSouthWest().lat, longitude: b.getSouthWest().lng },
      });
    },
  });

  // Bounds iniziali
  useEffect(() => {
    const b = map.getBounds();
    onBoundsChange({
      northEast: { latitude: b.getNorthEast().lat, longitude: b.getNorthEast().lng },
      southWest: { latitude: b.getSouthWest().lat, longitude: b.getSouthWest().lng },
    });
  }, []);

  return null;
}

// SVG icona alert per segnalazione
function reportAlertSVG(statusColor: string): string {
  return `
    <div style="
      width: 32px; height: 40px;
      display: flex; flex-direction: column;
      align-items: center;
    ">
      <div style="
        width: 32px; height: 32px;
        border-radius: 50%;
        background: ${statusColor};
        border: 2.5px solid white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
        display: flex; align-items: center; justify-content: center;
      ">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
          <path d="M12 2L1 21h22L12 2zm0 4l7.53 13H4.47L12 6zm-1 5v4h2v-4h-2zm0 6v2h2v-2h-2z"/>
        </svg>
      </div>
      <div style="
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid ${statusColor};
        margin-top: -1px;
      "></div>
    </div>
  `;
}

// Crea DivIcon per segnalazione
function createReportIcon(status: string): L.DivIcon {
  const color = REPORT_STATUS_COLORS[status] || '#FF9500';
  return L.divIcon({
    className: `report-marker-icon ${status}`,
    html: reportAlertSVG(color),
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -42],
  });
}

// Contenuto popup segnalazione
function reportPopupHTML(report: Report): string {
  const color = REPORT_STATUS_COLORS[report.status] || '#FF9500';
  const statusLabel = report.status === 'sent' ? 'Inviata' : 'In lavorazione';
  const date = new Date(report.createdAt).toLocaleDateString('it-IT', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  });

  return `
    <div style="padding: 12px; font-family: Inter, -apple-system, sans-serif;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <span style="
          background: ${color}20; color: ${color};
          font-size: 12px; font-weight: 600;
          padding: 2px 8px; border-radius: 999px;
        ">${statusLabel}</span>
        <span style="font-size: 12px; color: #8E8E93;">+${report.xp} XP</span>
      </div>
      <div style="font-size: 14px; font-weight: 500; color: #1C1C1E; margin-bottom: 4px;">
        ${report.address}
      </div>
      <div style="font-size: 12px; color: #8E8E93;">${date}</div>
      ${report.photo ? `<img src="${report.photo}" style="width: 100%; height: 80px; object-fit: cover; border-radius: 8px; margin-top: 8px;" />` : ''}
    </div>
  `;
}

// Marker segnalazione con popup
function ReportMarker({ report, onSelect }: {
  report: Report;
  onSelect: (report: Report) => void;
}) {
  const icon = createReportIcon(report.status);

  return (
    <Marker
      position={[report.lat, report.lng]}
      icon={icon}
      eventHandlers={{
        click: () => onSelect(report),
      }}
    >
      <Popup className="report-popup">
        <div dangerouslySetInnerHTML={{ __html: reportPopupHTML(report) }} />
      </Popup>
    </Marker>
  );
}

interface WebMapProps {
  trucks: TruckState[];
  reports: Report[];
  selectedTruck: TruckState | null;
  truckHistory: TruckState[];
  onSelectTruck: (truck: TruckState) => void;
  onSelectReport: (report: Report) => void;
  onDeselect: () => void;
  onBoundsChange: (bounds: { northEast: { latitude: number; longitude: number }; southWest: { latitude: number; longitude: number } }) => void;
}

export default function WebMap({
  trucks,
  reports,
  selectedTruck,
  truckHistory,
  onSelectTruck,
  onSelectReport,
  onDeselect,
  onBoundsChange,
}: WebMapProps) {
  useEffect(() => {
    injectCSS();
  }, []);

  const handleMapClick = useCallback(() => {
    onDeselect();
  }, [onDeselect]);

  return (
    <MapContainer
      center={[ROMA_REGION.latitude, ROMA_REGION.longitude]}
      zoom={14}
      style={{ width: '100%', height: '100%' }}
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <BoundsTracker onBoundsChange={onBoundsChange} />
      <MapClickHandler onClick={handleMapClick} />

      {trucks.map((truck) => (
        <AnimatedMarker
          key={truck.id}
          truck={truck}
          isSelected={selectedTruck?.truck_id === truck.truck_id}
          onSelect={onSelectTruck}
        />
      ))}

      {/* Marker di test hardcoded */}
      <Marker
        position={[41.9028, 12.4964]}
        icon={createReportIcon('sent')}
      />

      {reports && reports.length > 0 ? reports.map((report) => (
        <ReportMarker
          key={report.id}
          report={report}
          onSelect={onSelectReport}
        />
      )) : null}

      {selectedTruck && truckHistory.length > 1 && (
        <Polyline
          positions={truckHistory.map((h) => [h.latitude, h.longitude] as [number, number])}
          pathOptions={{
            color: wasteTypeColors[selectedTruck.waste_type],
            weight: 3,
            dashArray: '6 3',
          }}
        />
      )}
    </MapContainer>
  );
}

// Gestisce il click sulla mappa per deselezionare
function MapClickHandler({ onClick }: { onClick: () => void }) {
  useMapEvents({
    click: onClick,
  });
  return null;
}
