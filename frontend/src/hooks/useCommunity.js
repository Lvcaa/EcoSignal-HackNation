import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getStats, joinChallenge } from '../api/community'

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
