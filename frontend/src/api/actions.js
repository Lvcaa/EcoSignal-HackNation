import client from './client'

export const getActions = () =>
  client.get('/actions')

export const completeAction = (actionId) =>
  client.post(`/actions/${actionId}/complete`)

export const logAction = (data) =>
  client.post('/actions/log', data)

export const getDailyActions = (date) =>
  client.get('/actions/daily', { params: { date } })

export const getWeeklySummary = () =>
  client.get('/actions/weekly')
