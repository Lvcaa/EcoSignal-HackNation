import client from './client'

export const getProfile = () =>
  client.get('/profile')

export const updateProfile = (data) =>
  client.patch('/profile', data)

export const submitOnboarding = (data) =>
  client.post('/profile/onboarding', data)
