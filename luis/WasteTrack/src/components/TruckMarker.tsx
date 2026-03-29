import React from 'react';
import { View, StyleSheet } from 'react-native';
import Svg, { Path, Rect, Circle } from 'react-native-svg';
import { TruckState } from '../types';
import { wasteTypeColors, colors } from '../config/theme';

interface TruckMarkerProps {
  truck: TruckState;
  isSelected: boolean;
}

// Icona camion stilizzata SVG
function TruckIcon({ color, size }: { color: string; size: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      {/* Cabina */}
      <Rect x="1" y="6" width="15" height="10" rx="2" fill={color} />
      {/* Cassone */}
      <Path d="M16 9h3l3 4v3h-6V9z" fill={color} opacity={0.8} />
      {/* Ruote */}
      <Circle cx="6" cy="17.5" r="1.5" fill={colors.textPrimary} />
      <Circle cx="18" cy="17.5" r="1.5" fill={colors.textPrimary} />
      {/* Finestrino */}
      <Rect x="3" y="8" width="5" height="3" rx="0.5" fill="white" opacity={0.9} />
    </Svg>
  );
}

export default function TruckMarker({ truck, isSelected }: TruckMarkerProps) {
  const color = wasteTypeColors[truck.waste_type];
  const markerSize = isSelected ? 48 : 40;

  return (
    <View style={[styles.container, isSelected && styles.selected, { width: markerSize, height: markerSize }]}>
      <View style={[styles.bubble, { backgroundColor: color + '20', borderColor: color }]}>
        <TruckIcon color={color} size={isSelected ? 28 : 24} />
      </View>
      {/* Puntino sotto il marker */}
      <View style={[styles.dot, { backgroundColor: color }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  bubble: {
    borderRadius: 12,
    borderWidth: 2,
    padding: 4,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'white',
  },
  selected: {
    transform: [{ scale: 1.15 }],
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 2,
  },
});
