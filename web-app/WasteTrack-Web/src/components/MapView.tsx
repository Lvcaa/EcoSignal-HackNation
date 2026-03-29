import { useCallback, useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Polyline, useMapEvents, useMap } from 'react-leaflet';
import type { Map as LeafletMap } from 'leaflet';
import { useTrucks } from '../hooks/useTrucks';
import { useReports } from '../hooks/useReports';
import type { MapBounds } from '../hooks/useTrucks';
import type { Report } from '../types';
import { wasteTypeColors, ROMA_CENTER, ROMA_ZOOM } from '../config/theme';
import TruckMarkerComponent from './TruckMarker';
import ReportMarkerComponent from './ReportMarker';
import FilterPills from './FilterPills';
import TruckDetailPanel from './TruckDetailPanel';
import ReportEdgeIndicators from './ReportEdgeIndicators';
import './MapView.css';

// Gestisce eventi mappa (bounds + click)
function MapEvents({ onBoundsChange, onMapClick }: {
  onBoundsChange: (bounds: MapBounds) => void;
  onMapClick: () => void;
}) {
  const map = useMap();

  useEffect(() => {
    const b = map.getBounds();
    onBoundsChange({
      north: b.getNorth(),
      south: b.getSouth(),
      east: b.getEast(),
      west: b.getWest(),
    });
  }, [map, onBoundsChange]);

  useMapEvents({
    moveend: () => {
      const b = map.getBounds();
      onBoundsChange({
        north: b.getNorth(),
        south: b.getSouth(),
        east: b.getEast(),
        west: b.getWest(),
      });
    },
    click: () => onMapClick(),
  });

  return null;
}

// Esegue fly-to quando panTarget cambia; espone closePopup via ref
function MapPanner({ target, mapRef }: { target: Report | null; mapRef: React.MutableRefObject<LeafletMap | null> }) {
  const map = useMap();

  useEffect(() => {
    mapRef.current = map;
  }, [map, mapRef]);

  useEffect(() => {
    if (target) {
      map.flyTo([target.lat, target.lng], 17, { duration: 1 });
    }
  }, [target, map]);

  return null;
}

export default function MapView_() {
  const {
    allTrucks,
    visibleTrucks,
    selectedTruck,
    truckHistory,
    filter,
    mapBounds,
    isOffline,
    isLoading,
    setFilter,
    setMapBounds,
    selectTruck,
  } = useTrucks();

  const { activeReports } = useReports();
  const [panTarget, setPanTarget] = useState<Report | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);

  const handleBoundsChange = useCallback(
    (bounds: MapBounds) => setMapBounds(bounds),
    [setMapBounds]
  );

  const handleMapClick = useCallback(() => {
    if (selectedTruck) selectTruck(null);
  }, [selectedTruck, selectTruck]);

  const handleFlyTo = useCallback((report: Report) => {
    mapRef.current?.closePopup();
    setPanTarget(report);
  }, []);

  // Resetta panTarget dopo il fly-to così può essere riusato
  useEffect(() => {
    if (panTarget) {
      const t = setTimeout(() => setPanTarget(null), 1500);
      return () => clearTimeout(t);
    }
  }, [panTarget]);

  return (
    <div className="map-container" ref={containerRef}>
      <MapContainer
        center={[ROMA_CENTER.lat, ROMA_CENTER.lng]}
        zoom={ROMA_ZOOM}
        className="leaflet-map"
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapEvents onBoundsChange={handleBoundsChange} onMapClick={handleMapClick} />
        <MapPanner target={panTarget} mapRef={mapRef} />

        {visibleTrucks.map((truck) => (
          <TruckMarkerComponent
            key={truck.truck_id}
            truck={truck}
            isSelected={selectedTruck?.truck_id === truck.truck_id}
            onClick={() => selectTruck(truck)}
          />
        ))}

        {activeReports.map((report) => (
          <ReportMarkerComponent
            key={report.id}
            report={report}
            onClick={() => {}}
          />
        ))}

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

      <FilterPills activeFilter={filter} onFilterChange={setFilter} />

      <div className="active-badge">
        🚛 {visibleTrucks.length}/{allTrucks.length} camion
      </div>

      {isOffline && (
        <div className="offline-banner">
          ☁️ Offline — dati non aggiornati
        </div>
      )}

      {isLoading && (
        <div className="loading-overlay">
          <div className="spinner" />
        </div>
      )}

      {!isLoading && allTrucks.length === 0 && !isOffline && (
        <div className="empty-state">
          <span className="empty-icon">🚛</span>
          <h3>Nessun camion attivo</h3>
          <p>I camion appariranno qui quando saranno in servizio</p>
        </div>
      )}

      <ReportEdgeIndicators
        newReports={activeReports}
        mapBounds={mapBounds}
        containerRef={containerRef}
        onFlyTo={handleFlyTo}
      />

      <TruckDetailPanel truck={selectedTruck} onClose={() => selectTruck(null)} />
    </div>
  );
}
