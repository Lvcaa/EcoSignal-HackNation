// Tipi allineati al backend van_management API

export type WasteType = 'organic' | 'paper' | 'plastic' | 'glass' | 'mixed';

// Risposta dal backend — stato attuale di un camion
export interface TruckState {
  id: number;
  truck_id: string;
  company_id: string | null;
  waste_type: WasteType;
  latitude: number;
  longitude: number;
  position_timestamp: string; // ISO 8601
  version: number;
  created_at: string; // ISO 8601
}

// Risposta fleet snapshot — GET /api/v1/trucks
export interface FleetResponse {
  success: boolean;
  message: string;
  data: TruckState[];
}

// Risposta singolo truck — GET /api/v1/trucks/{id}/latest
export interface TruckLatestResponse {
  success: boolean;
  message: string;
  data: TruckState;
}

// Risposta history — GET /api/v1/trucks/{id}/history
export interface TruckHistoryResponse {
  success: boolean;
  message: string;
  data: {
    truck_id: string;
    total: number;
    page: number;
    page_size: number;
    records: TruckState[];
  };
}

// Modelli frontend — mock per segnalazioni, utenti, achievement

export type ReportStatus = 'sent' | 'in_progress' | 'resolved';

export interface Report {
  id: string;
  userId: string;
  binId: string;
  lat: number;
  lng: number;
  address: string;
  photo?: string;
  status: ReportStatus;
  xp: number;
  createdAt: string; // ISO 8601
}

export interface Achievement {
  id: string;
  label: string;
  description: string;
  icon: string; // nome icona Material
  unlockedAt?: string; // assente = bloccato
}

export interface User {
  id: string;
  name: string;
  avatar: string;
  xp: number;
  level: number;
  title: string;
  badges: Achievement[];
}

export interface LeaderboardEntry {
  rank: number;
  user: Pick<User, 'id' | 'name' | 'avatar' | 'level'>;
  points: number;
  trend?: number; // percentuale variazione (positiva o negativa)
}
