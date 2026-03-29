import React, { useCallback } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Platform } from 'react-native';
import * as Haptics from 'expo-haptics';
import { Ionicons } from '@expo/vector-icons';

import FilterPills from '../components/FilterPills';
import TruckBottomSheet from '../components/TruckBottomSheet';
import { useTrucks } from '../hooks/useTrucks';
import { useReports } from '../hooks/useReports';
import { colors, fonts, spacing, borderRadius, wasteTypeColors, ROMA_REGION } from '../config/theme';
import { TruckState, Report } from '../types';

// Import condizionali per piattaforma
let MapView: any = View;
let MarkerAnimated: any = View;
let Polyline: any = View;
let TruckMarkerIcon: any = View;
let AnimatedRegion: any = null;
let WebMap: any = null;
let WebTruckDetail: any = null;
let WebReportDetail: any = null;

if (Platform.OS === 'web') {
  WebMap = require('../components/WebMap').default;
  WebTruckDetail = require('../components/WebTruckDetail').default;
  WebReportDetail = require('../components/WebReportDetail').default;
} else {
  const Maps = require('react-native-maps');
  MapView = Maps.default;
  MarkerAnimated = Maps.Marker.Animated || Maps.MarkerAnimated;
  Polyline = Maps.Polyline;
  AnimatedRegion = Maps.AnimatedRegion;
  TruckMarkerIcon = require('../components/TruckMarker').default;
}

// Anima il marker tra posizioni successive con interpolazione nativa.
// Su iOS usa timing() (affidabile), su Android usa spring() (timing e' buggato).
function AnimatedTruckMarker({ truck, isSelected, onPress }: {
  truck: TruckState;
  isSelected: boolean;
  onPress: () => void;
}) {
  const coordinateRef = React.useRef<any>(
    AnimatedRegion
      ? new AnimatedRegion({
          latitude: truck.latitude,
          longitude: truck.longitude,
          latitudeDelta: 0,
          longitudeDelta: 0,
        })
      : null
  );

  React.useEffect(() => {
    if (!coordinateRef.current) return;

    const newCoord = {
      latitude: truck.latitude,
      longitude: truck.longitude,
      latitudeDelta: 0,
      longitudeDelta: 0,
      useNativeDriver: false,
    };

    if (Platform.OS === 'android') {
      // Su Android timing() e' rotto — spring() funziona correttamente
      coordinateRef.current.spring({
        ...newCoord,
        friction: 50,
        tension: 20,
      }).start();
    } else {
      // Su iOS timing() funziona bene
      coordinateRef.current.timing({
        ...newCoord,
        duration: 1000,
      }).start();
    }
  }, [truck.latitude, truck.longitude]);

  return (
    <MarkerAnimated
      coordinate={coordinateRef.current}
      onPress={onPress}
      tracksViewChanges={isSelected}
      anchor={{ x: 0.5, y: 0.5 }}
    >
      <TruckMarkerIcon truck={truck} isSelected={isSelected} />
    </MarkerAnimated>
  );
}

export default function MapScreen() {
  const {
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
  } = useTrucks();

  const mapRef = React.useRef<any>(null);

  // Aggiorna i bounds quando la mappa si muove
  const updateBounds = useCallback(async () => {
    if (!mapRef.current) return;
    try {
      const boundaries = await mapRef.current.getMapBoundaries();
      setMapBounds({
        northEast: boundaries.northEast,
        southWest: boundaries.southWest,
      });
    } catch {
      // Ignora errori — mostra tutti i camion come fallback
    }
  }, [setMapBounds]);

  const totalCount = allTrucks.length;

  const handleMarkerPress = (truck: TruckState) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    selectTruck(truck);
  };

  const handleSheetClose = () => {
    selectTruck(null);
  };

  // Reports per la mappa
  const { reports } = useReports();
  const activeReports = reports.filter((r) => r.status !== 'resolved');
  const [selectedReport, setSelectedReport] = React.useState<Report | null>(null);

  // Seleziona report → deseleziona camion e viceversa
  const handleSelectReport = (report: Report) => {
    setSelectedReport(report);
    selectTruck(null);
  };
  const handleSelectTruckWeb = (truck: TruckState) => {
    selectTruck(truck);
    setSelectedReport(null);
  };
  const handleDeselectAll = () => {
    selectTruck(null);
    setSelectedReport(null);
  };

  // Versione web — Leaflet
  if (Platform.OS === 'web') {
    return (
      <View style={styles.container}>
        <WebMap
          trucks={filteredTrucks}
          reports={activeReports}
          selectedTruck={selectedTruck}
          truckHistory={truckHistory}
          onSelectTruck={handleSelectTruckWeb}
          onSelectReport={handleSelectReport}
          onDeselect={handleDeselectAll}
          onBoundsChange={(bounds: any) => setMapBounds(bounds)}
        />

        <FilterPills activeFilter={filter} onFilterChange={setFilter} />

        <View style={styles.activeBadge}>
          <Ionicons name="bus" size={14} color={colors.primaryDark} />
          <Text style={styles.activeBadgeText}>
            {filteredTrucks.length}/{totalCount} camion
          </Text>
        </View>

        {isOffline && (
          <View style={styles.offlineBanner}>
            <Ionicons name="cloud-offline" size={16} color={colors.white} />
            <Text style={styles.offlineText}>Offline — dati non aggiornati</Text>
          </View>
        )}

        {isLoading && (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator size="large" color={colors.primary} />
          </View>
        )}

        <WebTruckDetail truck={selectedTruck} onClose={handleDeselectAll} />
        <WebReportDetail report={selectedReport} onClose={handleDeselectAll} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={StyleSheet.absoluteFillObject}
        initialRegion={ROMA_REGION}
        showsUserLocation
        showsMyLocationButton={false}
        onRegionChangeComplete={() => updateBounds()}
        onMapReady={() => updateBounds()}
        onPress={() => { if (selectedTruck) handleSheetClose(); }}
      >
        {filteredTrucks.map((truck) => (
          <AnimatedTruckMarker
            key={truck.id}
            truck={truck}
            isSelected={selectedTruck?.truck_id === truck.truck_id}
            onPress={() => handleMarkerPress(truck)}
          />
        ))}

        {selectedTruck && truckHistory.length > 1 && (
          <Polyline
            coordinates={truckHistory.map((h) => ({
              latitude: h.latitude,
              longitude: h.longitude,
            }))}
            strokeColor={wasteTypeColors[selectedTruck.waste_type]}
            strokeWidth={3}
            lineDashPattern={[6, 3]}
          />
        )}
      </MapView>

      <FilterPills activeFilter={filter} onFilterChange={setFilter} />

      <View style={styles.activeBadge}>
        <Ionicons name="bus" size={14} color={colors.primaryDark} />
        <Text style={styles.activeBadgeText}>
          {filteredTrucks.length}/{totalCount} camion
        </Text>
      </View>

      {isOffline && (
        <View style={styles.offlineBanner}>
          <Ionicons name="cloud-offline" size={16} color={colors.white} />
          <Text style={styles.offlineText}>Offline — dati non aggiornati</Text>
        </View>
      )}

      {isLoading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      )}

      {!isLoading && allTrucks.length === 0 && (
        <View style={styles.emptyState}>
          <Ionicons name="bus-outline" size={48} color={colors.textSecondary} />
          <Text style={styles.emptyTitle}>Nessun camion attivo</Text>
          <Text style={styles.emptySubtitle}>
            I camion appariranno qui quando saranno in servizio
          </Text>
        </View>
      )}

      <TruckBottomSheet truck={selectedTruck} onClose={handleSheetClose} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  activeBadge: {
    position: 'absolute',
    top: 60,
    right: spacing.lg,
    backgroundColor: colors.white,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    zIndex: 10,
  },
  activeBadgeText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.primaryDark,
  },
  offlineBanner: {
    position: 'absolute',
    top: 110,
    left: spacing.lg,
    right: spacing.lg,
    backgroundColor: colors.error,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.sm,
    zIndex: 10,
  },
  offlineText: {
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    color: colors.white,
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255,255,255,0.7)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 5,
  },
  emptyState: {
    position: 'absolute',
    bottom: 140,
    left: spacing.xxl,
    right: spacing.xxl,
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    padding: spacing.xxl,
    alignItems: 'center',
    gap: spacing.sm,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  emptyTitle: {
    fontFamily: fonts.headlineSemiBold,
    fontSize: 18,
    color: colors.textPrimary,
  },
  emptySubtitle: {
    fontFamily: fonts.bodyRegular,
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  webFallback: {
    flex: 1,
    paddingTop: 120,
    paddingHorizontal: spacing.xl,
    alignItems: 'center',
    gap: spacing.md,
  },
});
