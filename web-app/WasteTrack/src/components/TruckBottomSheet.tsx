import React, { useCallback, useMemo, useRef, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import BottomSheet, { BottomSheetView } from '@gorhom/bottom-sheet';
import { TruckState } from '../types';
import { colors, fonts, spacing, borderRadius, wasteTypeColors, wasteTypeLabels } from '../config/theme';

interface TruckBottomSheetProps {
  truck: TruckState | null;
  onClose: () => void;
}

export default function TruckBottomSheet({ truck, onClose }: TruckBottomSheetProps) {
  const bottomSheetRef = useRef<BottomSheet>(null);
  const snapPoints = useMemo(() => ['30%', '50%'], []);

  useEffect(() => {
    if (truck) {
      bottomSheetRef.current?.snapToIndex(0);
    } else {
      bottomSheetRef.current?.close();
    }
  }, [truck]);

  const handleSheetChanges = useCallback(
    (index: number) => {
      if (index === -1) {
        onClose();
      }
    },
    [onClose]
  );

  const wasteColor = truck ? wasteTypeColors[truck.waste_type] : colors.primary;
  const timeStr = truck
    ? new Date(truck.position_timestamp).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <BottomSheet
      ref={bottomSheetRef}
      index={-1}
      snapPoints={snapPoints}
      onChange={handleSheetChanges}
      enablePanDownToClose
      backgroundStyle={styles.background}
      handleIndicatorStyle={styles.handle}
    >
      <BottomSheetView style={styles.content}>
        {!truck ? null : (
        <>
        {/* Header */}
        <View style={styles.header}>
          <View style={[styles.wasteTypeBadge, { backgroundColor: wasteColor + '20' }]}>
            <View style={[styles.wasteTypeDot, { backgroundColor: wasteColor }]} />
            <Text style={[styles.wasteTypeText, { color: wasteColor }]}>
              {wasteTypeLabels[truck.waste_type]}
            </Text>
          </View>
          <Text style={styles.truckId}>{truck.truck_id}</Text>
        </View>

        {/* Dettagli */}
        <View style={styles.details}>
          <DetailRow label="Posizione" value={`${truck.latitude.toFixed(4)}, ${truck.longitude.toFixed(4)}`} />
          <DetailRow label="Ultimo aggiornamento" value={timeStr} />
          <DetailRow label="Versione dati" value={`v${truck.version}`} />
          {truck.company_id && <DetailRow label="Azienda" value={truck.company_id} />}
        </View>

        {/* Status indicator */}
        <View style={styles.statusRow}>
          <View style={[styles.statusDot, { backgroundColor: colors.success }]} />
          <Text style={styles.statusText}>In movimento</Text>
        </View>
        </>
        )}
      </BottomSheetView>
    </BottomSheet>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  background: {
    backgroundColor: colors.white,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 8,
  },
  handle: {
    backgroundColor: colors.border,
    width: 36,
    height: 4,
  },
  content: {
    padding: spacing.xl,
    paddingTop: spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.lg,
  },
  wasteTypeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    gap: spacing.xs,
  },
  wasteTypeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  wasteTypeText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
  },
  truckId: {
    fontFamily: fonts.headlineBold,
    fontSize: 18,
    color: colors.textPrimary,
  },
  details: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    gap: spacing.md,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontFamily: fonts.bodyRegular,
    fontSize: 14,
    color: colors.textSecondary,
  },
  detailValue: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.textPrimary,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.lg,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.textPrimary,
  },
});
