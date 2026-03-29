import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { WasteType } from '../types';
import { colors, fonts, spacing, borderRadius, wasteTypeColors, wasteTypeLabels } from '../config/theme';

interface FilterPillsProps {
  activeFilter: WasteType | null;
  onFilterChange: (filter: WasteType | null) => void;
}

const FILTERS: { key: WasteType | null; label: string }[] = [
  { key: null, label: 'Tutti' },
  { key: 'organic', label: wasteTypeLabels.organic },
  { key: 'paper', label: wasteTypeLabels.paper },
  { key: 'plastic', label: wasteTypeLabels.plastic },
  { key: 'glass', label: wasteTypeLabels.glass },
  { key: 'mixed', label: wasteTypeLabels.mixed },
];

export default function FilterPills({ activeFilter, onFilterChange }: FilterPillsProps) {
  return (
    <View style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.scroll}>
        {FILTERS.map((f) => {
          const isActive = f.key === activeFilter;
          const pillColor = f.key ? wasteTypeColors[f.key] : colors.primaryDark;

          return (
            <TouchableOpacity
              key={f.key ?? 'all'}
              style={[
                styles.pill,
                isActive && { backgroundColor: pillColor },
                !isActive && styles.pillInactive,
              ]}
              onPress={() => onFilterChange(f.key)}
              activeOpacity={0.7}
            >
              <Text style={[styles.pillText, isActive && styles.pillTextActive]}>
                {f.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 60,
    left: 0,
    right: 0,
    zIndex: 10,
  },
  scroll: {
    paddingHorizontal: spacing.lg,
    gap: spacing.sm,
  },
  pill: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
  },
  pillInactive: {
    backgroundColor: colors.white,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  pillText: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.textPrimary,
  },
  pillTextActive: {
    color: colors.white,
    fontFamily: fonts.bodySemiBold,
  },
});
