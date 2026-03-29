import axios from 'axios'

// Separate axios instance — no auth token needed for chat onboarding
const chatClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export const chatOnboarding = (messages, extracted_data = {}) =>
  chatClient.post('/chat/onboarding', { messages, extracted_data }, { timeout: 60_000 })
