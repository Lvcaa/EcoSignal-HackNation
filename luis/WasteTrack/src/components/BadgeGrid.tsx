import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Achievement } from '../types';
import { colors, fonts, spacing, borderRadius } from '../config/theme';

interface BadgeGridProps {
  badges: Achievement[];
  allAchievements: Achievement[];
}

// Mappa icone achievement a Ionicons
const ICON_MAP: Record<string, keyof typeof Ionicons.glyphMap> = {
  'flag': 'flag',
  'military-tech': 'medal',
  'auto-awesome': 'star',
  'local-fire-department': 'flame',
  'volunteer-activism': 'heart',
  'recycling': 'leaf',
};

export default function BadgeGrid({ badges, allAchievements }: BadgeGridProps) {
  const unlockedIds = new Set(badges.map((b) => b.id));

  return (
    <View style={styles.grid}>
      {allAchievements.map((achievement) => {
        const unlocked = unlockedIds.has(achievement.id);
        const iconName = ICON_MAP[achievement.icon] ?? 'ribbon';

        return (
          <View key={achievement.id} style={[styles.badge, !unlocked && styles.locked]}>
            <View style={[styles.iconContainer, unlocked ? styles.iconUnlocked : styles.iconLocked]}>
              <Ionicons
                name={iconName}
                size={24}
                color={unlocked ? colors.primaryDark : colors.textSecondary}
              />
            </View>
            <Text style={[styles.label, !unlocked && styles.labelLocked]} numberOfLines={1}>
              {achievement.label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  badge: {
    width: '30%',
    alignItems: 'center',
    gap: spacing.xs,
  },
  locked: {
    opacity: 0.5,
  },
  iconContainer: {
    width: 52,
    height: 52,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconUnlocked: {
    backgroundColor: colors.primary + '25',
  },
  iconLocked: {
    backgroundColor: colors.surface,
  },
  label: {
    fontFamily: fonts.bodyMedium,
    fontSize: 11,
    color: colors.textPrimary,
    textAlign: 'center',
  },
  labelLocked: {
    color: colors.textSecondary,
  },
});
