import { useState, useEffect, useRef, useCallback } from 'react';
import type { TruckState, FleetResponse, TruckLatestResponse, TruckHistoryResponse, WasteType } from '../types';
import { apiFetch } from '../config/api';

const POLL_INTERVAL = 1000;

export type MapBounds = {
  north: number;
  south: number;
  east: number;
  west: number;
};

export function useTrucks() {
  const [allTrucks, setAllTrucks] = useState<TruckState[]>([]);
  const [selectedTruck, setSelectedTruck] = useState<TruckState | null>(null);
  const [truckHistory, setTruckHistory] = useState<TruckState[]>([]);
  const [filter, setFilter] = useState<WasteType | null>(null);
  const [mapBounds, setMapBounds] = useState<MapBounds | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // 1) Fetch iniziale — tutti i camion, una volta sola
  useEffect(() => {
    (async () => {
      try {
        const response = await apiFetch<FleetResponse>('/api/v1/trucks');
        setAllTrucks(response.data);
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
        t.latitude >= mapBounds.south &&
        t.latitude <= mapBounds.north &&
        t.longitude >= mapBounds.west &&
        t.longitude <= mapBounds.east
      )
    : filteredTrucks;

  // 2) Polling ogni 1s — solo i camion visibili
  const visibleIdsRef = useRef<string[]>([]);
  visibleIdsRef.current = visibleTrucks.map((t) => t.truck_id);

  useEffect(() => {
    if (isLoading || allTrucks.length === 0) return;

    const pollPositions = async () => {
      const ids = visibleIdsRef.current;
      if (ids.length === 0) return;

      try {
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
              if (idx !== -1) updated[idx] = newData;
            }
          });
          return updated;
        });

        setSelectedTruck((prev) => {
          if (!prev) return null;
          const match = results.find(
            (r) => r.status === 'fulfilled' && r.value.data.truck_id === prev.truck_id
          );
          return match && match.status === 'fulfilled' ? match.value.data : prev;
        });

        setIsOffline(false);
      } catch {
        setIsOffline(true);
      }
    };

    const interval = setInterval(pollPositions, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [isLoading, allTrucks.length]);

  // Fetch history per polyline
  const selectTruck = useCallback(async (truck: TruckState | null) => {
    setSelectedTruck(truck);
    if (truck) {
      try {
        const response = await apiFetch<TruckHistoryResponse>(
          `/api/v1/trucks/${truck.truck_id}/history?page=1&page_size=200`
        );
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
  };
}
