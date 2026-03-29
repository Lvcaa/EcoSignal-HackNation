export type WasteType = 'organic' | 'paper' | 'plastic' | 'glass' | 'mixed';

export type TruckState = {
  id: number;
  truck_id: string;
  company_id: string | null;
  waste_type: WasteType;
  latitude: number;
  longitude: number;
  position_timestamp: string;
  version: number;
  created_at: string;
};

export type FleetResponse = {
  success: boolean;
  message: string;
  data: TruckState[];
};

export type TruckLatestResponse = {
  success: boolean;
  message: string;
  data: TruckState;
};

export type TruckHistoryResponse = {
  success: boolean;
  message: string;
  data: {
    truck_id: string;
    total: number;
    page: number;
    page_size: number;
    records: TruckState[];
  };
};

export type ReportStatus = 'sent' | 'in_progress' | 'resolved';

export type Report = {
  id: string;
  userId: string;
  binId: string;
  lat: number;
  lng: number;
  address: string;
  photo?: string;
  status: ReportStatus;
  xp: number;
  createdAt: string;
};
