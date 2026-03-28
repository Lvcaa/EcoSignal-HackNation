import client from './client'

export const getStats = () =>
  client.get('/community/stats')

export const joinChallenge = () =>
  client.post('/community/challenge/join')
