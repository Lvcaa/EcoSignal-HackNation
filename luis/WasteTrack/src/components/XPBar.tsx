import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, fonts, spacing, borderRadius } from '../config/theme';

interface XPBarProps {
  currentXP: number;
  maxXP: number;
  progress: number; // 0-1
}

export default function XPBar({ currentXP, maxXP, progress }: XPBarProps) {
  return (
    <View style={styles.container}>
      <View style={styles.labelRow}>
        <Text style={styles.label}>Progresso XP</Text>
        <Text style={styles.values}>
          {currentXP.toLocaleString()} / {maxXP.toLocaleString()}
        </Text>
      </View>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${Math.min(progress * 100, 100)}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.sm,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.textSecondary,
  },
  values: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.textPrimary,
  },
  track: {
    height: 8,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: borderRadius.full,
  },
});
