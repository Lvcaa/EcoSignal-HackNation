import client from './client'

export const analyzeImage = (image_base64, analysis_type, user_description) =>
  client.post('/image/analyze', { image_base64, analysis_type, user_description })
