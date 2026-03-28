import client from './client'

export const register = (email, password, display_name) =>
  client.post('/auth/register', { email, password, display_name })

export const login = (email, password) =>
  client.post('/auth/login', { email, password })

export const refresh = (refresh_token) =>
  client.post('/auth/refresh', { refresh_token })
