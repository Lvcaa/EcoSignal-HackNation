import client from './client'

export const register = (email, password, display_name) =>
  client.post('/auth/register', { email, password, display_name })

export const login = (email, password) =>
  client.post('/auth/login', { email, password })

export const refresh = (refresh_token) =>
  client.post('/auth/refresh', { refresh_token })

export const listUsers = (limit = 50) =>
  client.get('/auth/users', { params: { limit } })

export const impersonate = (userId) =>
  client.post(`/auth/impersonate/${userId}`)
