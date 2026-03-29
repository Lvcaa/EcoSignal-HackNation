import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

import ReportCard from '../components/ReportCard';
import { useReports } from '../hooks/useReports';
import { colors, fonts, spacing, borderRadius } from '../config/theme';

export default function ReportsScreen() {
  const { reports, totalPoints, resolvedCount } = useReports();
  const insets = useSafeAreaInsets();

  const handleNewReport = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    Alert.alert(
      'Nuova Segnalazione',
      'Il flusso completo con camera e GPS sara\' disponibile nella prossima versione.',
      [{ text: 'OK' }]
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Segnalazioni</Text>
        <Text style={styles.subtitle}>Monitora le tue contribuzioni alla citta'</Text>
      </View>

      {/* Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{totalPoints}</Text>
          <Text style={styles.statLabel}>Punti totali</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{resolvedCount}</Text>
          <Text style={styles.statLabel}>Risolte</Text>
        </View>
      </View>

      {/* Lista report */}
      <Text style={styles.sectionTitle}>Report recenti</Text>
      <FlatList
        data={reports}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <ReportCard report={item} />}
        contentContainerStyle={styles.list}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        showsVerticalScrollIndicator={false}
      />

      {/* FAB */}
      <TouchableOpacity
        style={[styles.fab, { bottom: 24 }]}
        onPress={handleNewReport}
        activeOpacity={0.8}
      >
        <Ionicons name="camera" size={28} color={colors.white} />
      </TouchableOpacity>
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
    paddingBottom: spacing.sm,
  },
  title: {
    fontFamily: fonts.headlineBold,
    fontSize: 28,
    color: colors.textPrimary,
  },
  subtitle: {
    fontFamily: fonts.bodyRegular,
    fontSize: 15,
    color: colors.textSecondary,
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing.xl,
    gap: spacing.md,
    marginTop: spacing.lg,
    marginBottom: spacing.xl,
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
  sectionTitle: {
    fontFamily: fonts.headlineSemiBold,
    fontSize: 18,
    color: colors.textPrimary,
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.md,
  },
  list: {
    paddingHorizontal: spacing.xl,
    paddingBottom: 100,
  },
  separator: {
    height: spacing.md,
  },
  fab: {
    position: 'absolute',
    right: spacing.xl,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.primaryDark,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
});
