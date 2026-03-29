import { useEffect, useRef } from 'react';
import { Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { TruckState } from '../types';
import { wasteTypeColors } from '../config/theme';

interface TruckMarkerProps {
  truck: TruckState;
  isSelected: boolean;
  onClick: () => void;
}

function createTruckIcon(color: string, isSelected: boolean): L.DivIcon {
  const size = isSelected ? 40 : 32;
  const border = isSelected ? '3px solid ' + color : '2px solid ' + color;

  return L.divIcon({
    className: 'truck-marker-icon',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background: ${color}20;
        border: ${border};
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
        ${isSelected ? 'box-shadow: 0 4px 12px ' + color + '40;' : ''}
      ">
        <svg width="${size * 0.6}" height="${size * 0.6}" viewBox="0 0 24 24" fill="none">
          <rect x="1" y="6" width="15" height="10" rx="2" fill="${color}"/>
          <path d="M16 9h3l3 4v3h-6V9z" fill="${color}" opacity="0.8"/>
          <circle cx="6" cy="17.5" r="1.5" fill="#333"/>
          <circle cx="18" cy="17.5" r="1.5" fill="#333"/>
          <rect x="3" y="8" width="5" height="3" rx="0.5" fill="white" opacity="0.9"/>
        </svg>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function TruckMarkerComponent({ truck, isSelected, onClick }: TruckMarkerProps) {
  const markerRef = useRef<L.Marker>(null);
  const color = wasteTypeColors[truck.waste_type];
  const icon = createTruckIcon(color, isSelected);

  // Animazione smooth della posizione
  useEffect(() => {
    const marker = markerRef.current;
    if (!marker) return;

    const target = L.latLng(truck.latitude, truck.longitude);
    const current = marker.getLatLng();

    if (current.lat === target.lat && current.lng === target.lng) return;

    // Interpola in 30 step su 800ms
    const steps = 30;
    const duration = 800;
    const latStep = (target.lat - current.lat) / steps;
    const lngStep = (target.lng - current.lng) / steps;
    let step = 0;

    const interval = setInterval(() => {
      step++;
      if (step >= steps) {
        marker.setLatLng(target);
        clearInterval(interval);
      } else {
        marker.setLatLng([
          current.lat + latStep * step,
          current.lng + lngStep * step,
        ]);
      }
    }, duration / steps);

    return () => clearInterval(interval);
  }, [truck.latitude, truck.longitude]);

  return (
    <Marker
      ref={markerRef}
      position={[truck.latitude, truck.longitude]}
      icon={icon}
      eventHandlers={{ click: onClick }}
    />
  );
}
