import React from 'react';
import { View, Text, Image, ScrollView, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import XPBar from '../components/XPBar';
import BadgeGrid from '../components/BadgeGrid';
import { useUser } from '../hooks/useUser';
import { useReports } from '../hooks/useReports';
import { ACHIEVEMENTS } from '../data/achievements';
import { XP_PER_LEVEL } from '../data/users';
import { colors, fonts, spacing, borderRadius } from '../config/theme';

export default function ProfileScreen() {
  const { user, xpProgress } = useUser();
  const { reports } = useReports();
  const insets = useSafeAreaInsets();

  // Ultime 3 attivita'
  const recentActivity = reports.slice(0, 3);

  return (
    <ScrollView style={[styles.container, { paddingTop: insets.top }]} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Profilo</Text>
      </View>

      {/* Avatar + info */}
      <View style={styles.profileSection}>
        <View style={styles.avatarWrapper}>
          <Image source={{ uri: user.avatar }} style={styles.avatar} />
          <View style={styles.verifiedBadge}>
            <Ionicons name="checkmark-circle" size={24} color={colors.primary} />
          </View>
        </View>
        <Text style={styles.name}>{user.name}</Text>
        <Text style={styles.levelTitle}>Livello {user.level} · {user.title}</Text>
      </View>

      {/* XP Bar */}
      <View style={styles.section}>
        <XPBar currentXP={user.xp} maxXP={XP_PER_LEVEL} progress={xpProgress} />
      </View>

      {/* Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{(user.xp * 10).toLocaleString()}</Text>
          <Text style={styles.statLabel}>Punti totali</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{reports.filter(r => r.status === 'resolved').length * 3}</Text>
          <Text style={styles.statLabel}>Kg deviati</Text>
        </View>
      </View>

      {/* Achievement */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Achievement</Text>
        <BadgeGrid badges={user.badges} allAchievements={ACHIEVEMENTS} />
      </View>

      {/* Attivita' recenti */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Attivita' recenti</Text>
        {recentActivity.map((report) => {
          const date = new Date(report.createdAt);
          const dateStr = date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' });

          const STATUS_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
            sent: 'paper-plane',
            in_progress: 'time',
            resolved: 'checkmark-circle',
          };
          const STATUS_COLORS: Record<string, string> = {
            sent: '#FF9500',
            in_progress: '#2196F3',
            resolved: '#4CAF50',
          };

          return (
            <View key={report.id} style={styles.activityRow}>
              <View style={[styles.activityIcon, { backgroundColor: STATUS_COLORS[report.status] + '15' }]}>
                <Ionicons
                  name={STATUS_ICONS[report.status]}
                  size={20}
                  color={STATUS_COLORS[report.status]}
                />
              </View>
              <View style={styles.activityInfo}>
                <Text style={styles.activityTitle}>{report.address}</Text>
                <Text style={styles.activityDate}>{dateStr}</Text>
              </View>
              <Text style={styles.activityXP}>+{report.xp} XP</Text>
            </View>
          );
        })}
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.lg,
    paddingBottom: spacing.sm,
  },
  headerTitle: {
    fontFamily: fonts.headlineBold,
    fontSize: 28,
    color: colors.textPrimary,
  },
  profileSection: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  avatarWrapper: {
    position: 'relative',
    marginBottom: spacing.md,
  },
  avatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    borderWidth: 3,
    borderColor: colors.primary,
  },
  verifiedBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: colors.white,
    borderRadius: borderRadius.full,
  },
  name: {
    fontFamily: fonts.headlineBold,
    fontSize: 22,
    color: colors.textPrimary,
  },
  levelTitle: {
    fontFamily: fonts.bodyMedium,
    fontSize: 15,
    color: colors.textSecondary,
    marginTop: 2,
  },
  section: {
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xxl,
  },
  sectionTitle: {
    fontFamily: fonts.headlineSemiBold,
    fontSize: 18,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing.xl,
    gap: spacing.md,
    marginBottom: spacing.xxl,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
  },
  statValue: {
    fontFamily: fonts.headlineBold,
    fontSize: 24,
    color: colors.primaryDark,
  },
  statLabel: {
    fontFamily: fonts.bodyRegular,
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  activityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.card,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    gap: spacing.md,
    marginBottom: spacing.sm,
  },
  activityIcon: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activityInfo: {
    flex: 1,
  },
  activityTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.textPrimary,
  },
  activityDate: {
    fontFamily: fonts.bodyRegular,
    fontSize: 12,
    color: colors.textSecondary,
  },
  activityXP: {
    fontFamily: fonts.headlineSemiBold,
    fontSize: 14,
    color: colors.primaryDark,
  },
});
