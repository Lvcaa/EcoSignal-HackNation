import client from './client'

export const getNarrative = () =>
  client.get('/narrative')
