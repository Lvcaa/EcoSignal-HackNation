import React, { useState } from 'react';
import { View, Text, Image, FlatList, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import BadgeGrid from '../components/BadgeGrid';
import { MOCK_LEADERBOARD } from '../data/users';
import { ACHIEVEMENTS } from '../data/achievements';
import { LeaderboardEntry } from '../types';
import { colors, fonts, spacing, borderRadius } from '../config/theme';

type Period = 'weekly' | 'monthly' | 'alltime';

const PERIODS: { key: Period; label: string }[] = [
  { key: 'weekly', label: 'Settimanale' },
  { key: 'monthly', label: 'Mensile' },
  { key: 'alltime', label: 'Sempre' },
];

const CURRENT_USER_ID = 'u1';

export default function LeaderboardScreen() {
  const [period, setPeriod] = useState<Period>('weekly');
  const insets = useSafeAreaInsets();

  const top3 = MOCK_LEADERBOARD.slice(0, 3);
  const rest = MOCK_LEADERBOARD.slice(3);

  return (
    <ScrollView style={[styles.container, { paddingTop: insets.top }]} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Classifica</Text>
      </View>

      {/* Segmented control */}
      <View style={styles.segmented}>
        {PERIODS.map((p) => (
          <TouchableOpacity
            key={p.key}
            style={[styles.segment, period === p.key && styles.segmentActive]}
            onPress={() => setPeriod(p.key)}
          >
            <Text style={[styles.segmentText, period === p.key && styles.segmentTextActive]}>
              {p.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Podio top 3 */}
      <View style={styles.podium}>
        {/* 2nd place */}
        <PodiumItem entry={top3[1]} position={2} />
        {/* 1st place */}
        <PodiumItem entry={top3[0]} position={1} />
        {/* 3rd place */}
        <PodiumItem entry={top3[2]} position={3} />
      </View>

      {/* Lista rank 4+ */}
      <View style={styles.listSection}>
        {rest.map((entry) => (
          <LeaderboardRow key={entry.user.id} entry={entry} isCurrentUser={entry.user.id === CURRENT_USER_ID} />
        ))}
      </View>

      {/* Achievement section */}
      <View style={styles.achievementSection}>
        <Text style={styles.sectionTitle}>Achievement</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.achievementScroll}>
            {ACHIEVEMENTS.map((a) => {
              const unlocked = !!a.unlockedAt;
              return (
                <View key={a.id} style={[styles.achievementChip, !unlocked && styles.achievementLocked]}>
                  <Ionicons
                    name={unlocked ? 'ribbon' : 'lock-closed'}
                    size={16}
                    color={unlocked ? colors.primaryDark : colors.textSecondary}
                  />
                  <Text style={[styles.achievementLabel, !unlocked && { color: colors.textSecondary }]}>
                    {a.label}
                  </Text>
                </View>
              );
            })}
          </View>
        </ScrollView>
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

// Componente podio singolo
function PodiumItem({ entry, position }: { entry: LeaderboardEntry; position: 1 | 2 | 3 }) {
  const isFirst = position === 1;
  const avatarSize = isFirst ? 72 : 56;
  const podiumHeight = isFirst ? 100 : position === 2 ? 70 : 55;

  const medalColors = { 1: '#FFD700', 2: '#C0C0C0', 3: '#CD7F32' };

  return (
    <View style={[styles.podiumItem, isFirst && styles.podiumFirst]}>
      {/* Avatar */}
      <View style={[styles.avatarContainer, { width: avatarSize, height: avatarSize }]}>
        <Image source={{ uri: entry.user.avatar }} style={[styles.avatar, { width: avatarSize, height: avatarSize }]} />
        {isFirst && (
          <View style={styles.crown}>
            <Ionicons name="trophy" size={16} color="#FFD700" />
          </View>
        )}
      </View>

      <Text style={styles.podiumName} numberOfLines={1}>{entry.user.name}</Text>
      <Text style={styles.podiumPoints}>{entry.points.toLocaleString()} kg</Text>

      {/* Piedistallo */}
      <View style={[styles.pedestal, { height: podiumHeight, backgroundColor: medalColors[position] + '30' }]}>
        <Text style={[styles.pedestalRank, { color: medalColors[position] }]}>{position}</Text>
      </View>
    </View>
  );
}

// Riga classifica
function LeaderboardRow({ entry, isCurrentUser }: { entry: LeaderboardEntry; isCurrentUser: boolean }) {
  return (
    <View style={[styles.row, isCurrentUser && styles.rowHighlight]}>
      <Text style={styles.rowRank}>{entry.rank}</Text>
      <Image source={{ uri: entry.user.avatar }} style={styles.rowAvatar} />
      <View style={styles.rowInfo}>
        <Text style={styles.rowName}>{entry.user.name}</Text>
        <Text style={styles.rowLevel}>Lv. {entry.user.level}</Text>
      </View>
      <View style={styles.rowRight}>
        <Text style={styles.rowPoints}>{entry.points.toLocaleString()} kg</Text>
        {entry.trend !== undefined && (
          <View style={styles.trendRow}>
            <Ionicons
              name={entry.trend >= 0 ? 'arrow-up' : 'arrow-down'}
              size={12}
              color={entry.trend >= 0 ? colors.success : colors.error}
            />
            <Text style={[styles.trendText, { color: entry.trend >= 0 ? colors.success : colors.error }]}>
              {Math.abs(entry.trend)}%
            </Text>
          </View>
        )}
      </View>
    </View>
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
    paddingBottom: spacing.md,
  },
  title: {
    fontFamily: fonts.headlineBold,
    fontSize: 28,
    color: colors.textPrimary,
  },
  segmented: {
    flexDirection: 'row',
    marginHorizontal: spacing.xl,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.sm,
    padding: 3,
    marginBottom: spacing.xl,
  },
  segment: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.sm - 2,
    alignItems: 'center',
  },
  segmentActive: {
    backgroundColor: colors.white,
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  segmentText: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.textSecondary,
  },
  segmentTextActive: {
    color: colors.textPrimary,
    fontFamily: fonts.bodySemiBold,
  },

  // Podio
  podium: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xxl,
    gap: spacing.md,
  },
  podiumItem: {
    alignItems: 'center',
    flex: 1,
  },
  podiumFirst: {
    marginBottom: 20,
  },
  avatarContainer: {
    borderRadius: borderRadius.full,
    overflow: 'visible',
    marginBottom: spacing.sm,
  },
  avatar: {
    borderRadius: borderRadius.full,
  },
  crown: {
    position: 'absolute',
    top: -12,
    alignSelf: 'center',
    backgroundColor: colors.white,
    borderRadius: borderRadius.full,
    padding: 2,
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  podiumName: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.textPrimary,
  },
  podiumPoints: {
    fontFamily: fonts.bodyRegular,
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  pedestal: {
    width: '100%',
    borderTopLeftRadius: borderRadius.sm,
    borderTopRightRadius: borderRadius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pedestalRank: {
    fontFamily: fonts.headlineBold,
    fontSize: 22,
  },

  // Lista
  listSection: {
    paddingHorizontal: spacing.xl,
    gap: spacing.sm,
    marginBottom: spacing.xxl,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.card,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    gap: spacing.md,
  },
  rowHighlight: {
    backgroundColor: colors.primary + '15',
    borderWidth: 1,
    borderColor: colors.primary + '40',
  },
  rowRank: {
    fontFamily: fonts.headlineBold,
    fontSize: 16,
    color: colors.textSecondary,
    width: 28,
    textAlign: 'center',
  },
  rowAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  rowInfo: {
    flex: 1,
  },
  rowName: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.textPrimary,
  },
  rowLevel: {
    fontFamily: fonts.bodyRegular,
    fontSize: 12,
    color: colors.textSecondary,
  },
  rowRight: {
    alignItems: 'flex-end',
  },
  rowPoints: {
    fontFamily: fonts.headlineSemiBold,
    fontSize: 15,
    color: colors.textPrimary,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  trendText: {
    fontFamily: fonts.bodyMedium,
    fontSize: 12,
  },

  // Achievement
  achievementSection: {
    paddingHorizontal: spacing.xl,
  },
  sectionTitle: {
    fontFamily: fonts.headlineSemiBold,
    fontSize: 18,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },
  achievementScroll: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  achievementChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.primary + '15',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
  },
  achievementLocked: {
    backgroundColor: colors.surface,
  },
  achievementLabel: {
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    color: colors.primaryDark,
  },
});
