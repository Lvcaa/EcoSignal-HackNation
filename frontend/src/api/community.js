import client from './client'

export const getStats = () =>
  client.get('/community/stats')

export const joinChallenge = () =>
  client.post('/community/challenge/join')

export const getLeaderboard = (zipCode) => {
  const params = {}
  if (zipCode) params.zip_code = zipCode
  return client.get('/community/leaderboard', { params })
}

export const getUserActions = (userId, date) => {
  const params = {}
  if (date) params.date = date
  return client.get(`/community/user/${userId}/actions`, { params })
}
