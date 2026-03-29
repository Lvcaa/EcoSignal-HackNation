// Design system — light mode adattato dai mockup

import { WasteType } from '../types';

export const colors = {
  background: '#FFFFFF',
  surface: '#F2F2F7',
  card: '#F8F8FA',
  primary: '#95d4ac',
  primaryDark: '#609d78',
  textPrimary: '#1C1C1E',
  textSecondary: '#8E8E93',
  white: '#FFFFFF',
  black: '#000000',
  error: '#FF3B30',
  success: '#34C759',
  border: '#E5E5EA',
  overlay: 'rgba(0, 0, 0, 0.05)',
} as const;

// Colori per tipo rifiuto — marker e filtri
export const wasteTypeColors: Record<WasteType, string> = {
  organic: '#4CAF50',
  paper: '#2196F3',
  plastic: '#FF9800',
  glass: '#9C27B0',
  mixed: '#78909C',
};

// Label italiane per tipo rifiuto
export const wasteTypeLabels: Record<WasteType, string> = {
  organic: 'Organico',
  paper: 'Carta',
  plastic: 'Plastica',
  glass: 'Vetro',
  mixed: 'Misto',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
} as const;

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  full: 999,
} as const;

export const fonts = {
  headlineBold: 'Manrope_700Bold' as const,
  headlineSemiBold: 'Manrope_600SemiBold' as const,
  headlineMedium: 'Manrope_500Medium' as const,
  bodyRegular: 'Inter_400Regular' as const,
  bodyMedium: 'Inter_500Medium' as const,
  bodySemiBold: 'Inter_600SemiBold' as const,
};

// Regione iniziale mappa — Roma
export const ROMA_REGION = {
  latitude: 41.9028,
  longitude: 12.4964,
  latitudeDelta: 0.05,
  longitudeDelta: 0.05,
};
