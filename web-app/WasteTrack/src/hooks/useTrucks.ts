import { useState, useEffect, useRef, useCallback } from 'react';
import { TruckState, FleetResponse, TruckLatestResponse, TruckHistoryResponse, WasteType } from '../types';
import { apiFetch } from '../config/api';

// Polling posizioni ogni 1 secondo
const POSITION_POLL_INTERVAL = 1000;

interface MapBounds {
  northEast: { latitude: number; longitude: number };
  southWest: { latitude: number; longitude: number };
}

interface UseTrucksResult {
  allTrucks: TruckState[];
  filteredTrucks: TruckState[];
  visibleTrucks: TruckState[];
  selectedTruck: TruckState | null;
  truckHistory: TruckState[];
  filter: WasteType | null;
  isOffline: boolean;
  isLoading: boolean;
  setFilter: (type: WasteType | null) => void;
  setMapBounds: (bounds: MapBounds | null) => void;
  selectTruck: (truck: TruckState | null) => void;
}

export function useTrucks(): UseTrucksResult {
  const [allTrucks, setAllTrucks] = useState<TruckState[]>([]);
  const [selectedTruck, setSelectedTruck] = useState<TruckState | null>(null);
  const [truckHistory, setTruckHistory] = useState<TruckState[]>([]);
  const [filter, setFilter] = useState<WasteType | null>(null);
  const [mapBounds, setMapBounds] = useState<MapBounds | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const lastTrucksRef = useRef<TruckState[]>([]);

  // 1) Fetch iniziale — tutti i camion, una volta sola
  useEffect(() => {
    (async () => {
      try {
        const response = await apiFetch<FleetResponse>('/api/v1/trucks');
        setAllTrucks(response.data);
        lastTrucksRef.current = response.data;
        setIsOffline(false);
      } catch {
        setIsOffline(true);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  // Filtra per waste_type
  const filteredTrucks = filter
    ? allTrucks.filter((t) => t.waste_type === filter)
    : allTrucks;

  // Filtra per viewport
  const visibleTrucks = mapBounds
    ? filteredTrucks.filter((t) =>
        t.latitude >= mapBounds.southWest.latitude &&
        t.latitude <= mapBounds.northEast.latitude &&
        t.longitude >= mapBounds.southWest.longitude &&
        t.longitude <= mapBounds.northEast.longitude
      )
    : filteredTrucks;

  // 2) Polling ogni 1s — solo i camion visibili (filtro + viewport)
  const visibleIdsRef = useRef<string[]>([]);
  visibleIdsRef.current = visibleTrucks.map((t) => t.truck_id);

  useEffect(() => {
    if (isLoading || allTrucks.length === 0) return;

    const pollPositions = async () => {
      const ids = visibleIdsRef.current;
      if (ids.length === 0) return;

      try {
        // Fetch parallelo di tutti i camion visibili
        const results = await Promise.allSettled(
          ids.map((id) =>
            apiFetch<TruckLatestResponse>(`/api/v1/trucks/${id}/latest`)
          )
        );

        setAllTrucks((prev) => {
          const updated = [...prev];
          results.forEach((result) => {
            if (result.status === 'fulfilled') {
              const newData = result.value.data;
              const idx = updated.findIndex((t) => t.truck_id === newData.truck_id);
              if (idx !== -1) {
                updated[idx] = newData;
              }
            }
          });
          lastTrucksRef.current = updated;
          return updated;
        });

        // Aggiorna il camion selezionato se presente
        setSelectedTruck((prev) => {
          if (!prev) return null;
          const match = results.find(
            (r) => r.status === 'fulfilled' && r.value.data.truck_id === prev.truck_id
          );
          if (match && match.status === 'fulfilled') {
            return match.value.data;
          }
          return prev;
        });

        setIsOffline(false);
      } catch {
        setIsOffline(true);
      }
    };

    const interval = setInterval(pollPositions, POSITION_POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [isLoading, allTrucks.length]);

  // Fetch history quando si seleziona un camion (per polyline)
  const selectTruck = useCallback(async (truck: TruckState | null) => {
    setSelectedTruck(truck);
    if (truck) {
      try {
        const response = await apiFetch<TruckHistoryResponse>(
          `/api/v1/trucks/${truck.truck_id}/history?page=1&page_size=200`
        );
        // Ordina dal piu' vecchio al piu' recente per la polyline
        setTruckHistory(response.data.records.reverse());
      } catch {
        setTruckHistory([]);
      }
    } else {
      setTruckHistory([]);
    }
  }, []);

  return {
    allTrucks,
    filteredTrucks,
    visibleTrucks,
    selectedTruck,
    truckHistory,
    filter,
    isOffline,
    isLoading,
    setFilter,
    setMapBounds,
    selectTruck,
  };
}
