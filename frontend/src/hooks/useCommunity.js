import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getStats, joinChallenge, getLeaderboard, getUserActions } from '../api/community'

export function useCommunityStats() {
  return useQuery({
    queryKey: ['community-stats'],
    queryFn: () => getStats().then((r) => r.data),
  })
}

export function useJoinChallenge() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => joinChallenge(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['community-stats'] })
    },
  })
}

export function useLeaderboard(zipCode) {
  return useQuery({
    queryKey: ['community-leaderboard', zipCode],
    queryFn: () => getLeaderboard(zipCode).then((r) => r.data),
  })
}

export function useUserActions(userId) {
  const today = new Date().toISOString().slice(0, 10)
  return useQuery({
    queryKey: ['community-user-actions', userId, today],
    queryFn: () => getUserActions(userId, today).then((r) => r.data),
    enabled: !!userId,
  })
}
