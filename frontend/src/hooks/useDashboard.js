import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { calculateFootprint, getHistory } from '../api/footprint'
import { getAirQuality } from '../api/envData'
import { getNarrative } from '../api/narrative'
import { getActions, completeAction, logAction, getDailyActions, getWeeklySummary } from '../api/actions'

export function useFootprint() {
  return useQuery({
    queryKey: ['footprint'],
    queryFn: () => calculateFootprint().then((r) => r.data),
  })
}

export function useFootprintHistory(weeks = 4) {
  return useQuery({
    queryKey: ['footprint-history', weeks],
    queryFn: () => getHistory(weeks).then((r) => r.data),
  })
}

export function useAirQuality() {
  return useQuery({
    queryKey: ['air-quality'],
    queryFn: () => getAirQuality().then((r) => r.data),
  })
}

export function useNarrative() {
  return useQuery({
    queryKey: ['narrative'],
    queryFn: () => getNarrative().then((r) => r.data),
    staleTime: 60_000,
  })
}

export function useActions() {
  return useQuery({
    queryKey: ['actions'],
    queryFn: () => getActions().then((r) => r.data),
  })
}

export function useCompleteAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (actionId) => completeAction(actionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['actions'] })
      qc.invalidateQueries({ queryKey: ['footprint'] })
    },
  })
}

export function useLogAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data) => logAction(data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['daily-actions'] })
      qc.invalidateQueries({ queryKey: ['weekly-summary'] })
      qc.invalidateQueries({ queryKey: ['footprint'] })
    },
  })
}

export function useDailyActions(date) {
  return useQuery({
    queryKey: ['daily-actions', date],
    queryFn: () => getDailyActions(date).then((r) => r.data),
  })
}

export function useWeeklySummary() {
  return useQuery({
    queryKey: ['weekly-summary'],
    queryFn: () => getWeeklySummary().then((r) => r.data),
  })
}
