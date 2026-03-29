import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Report } from '../types';
import { colors, fonts, spacing, borderRadius } from '../config/theme';

interface ReportCardProps {
  report: Report;
}

const STATUS_CONFIG: Record<Report['status'], { label: string; color: string; bg: string }> = {
  sent: { label: 'Inviata', color: '#FF9500', bg: '#FFF3E0' },
  in_progress: { label: 'In lavorazione', color: '#2196F3', bg: '#E3F2FD' },
  resolved: { label: 'Risolta', color: '#4CAF50', bg: '#E8F5E9' },
};

export default function ReportCard({ report }: ReportCardProps) {
  const status = STATUS_CONFIG[report.status];
  const date = new Date(report.createdAt);
  const dateStr = date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' });
  const timeStr = date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });

  return (
    <View style={styles.card}>
      {/* Thumbnail */}
      {report.photo ? (
        <Image source={{ uri: report.photo }} style={styles.thumbnail} />
      ) : (
        <View style={[styles.thumbnail, styles.noPhoto]}>
          <Ionicons name="camera-outline" size={24} color={colors.textSecondary} />
        </View>
      )}

      {/* Contenuto */}
      <View style={styles.content}>
        <View style={styles.topRow}>
          <Text style={styles.address} numberOfLines={1}>{report.address}</Text>
          <View style={[styles.statusBadge, { backgroundColor: status.bg }]}>
            <Text style={[styles.statusText, { color: status.color }]}>{status.label}</Text>
          </View>
        </View>

        <View style={styles.metaRow}>
          <Ionicons name="location-outline" size={14} color={colors.textSecondary} />
          <Text style={styles.metaText}>{dateStr} · {timeStr}</Text>
        </View>

        <View style={styles.xpRow}>
          <Ionicons name="flash" size={14} color={colors.primaryDark} />
          <Text style={styles.xpText}>+{report.xp} XP</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    backgroundColor: colors.white,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    gap: spacing.md,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  thumbnail: {
    width: 64,
    height: 64,
    borderRadius: borderRadius.sm,
  },
  noPhoto: {
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
    gap: spacing.xs,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  address: {
    fontFamily: fonts.headlineSemiBold,
    fontSize: 15,
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },
  statusBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  statusText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 11,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontFamily: fonts.bodyRegular,
    fontSize: 13,
    color: colors.textSecondary,
  },
  xpRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  xpText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.primaryDark,
  },
});
