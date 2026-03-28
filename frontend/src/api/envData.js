import client from './client'

export const getAirQuality = () =>
  client.get('/env/air-quality')

export const getClimateContext = () =>
  client.get('/env/climate-context')
