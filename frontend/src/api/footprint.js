import client from './client'

export const calculateFootprint = () =>
  client.post('/footprint/calculate')

export const getHistory = (weeks = 4) =>
  client.get('/footprint/history', { params: { weeks } })
