import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { useNotificationStore } from '../store/notifications'
import { useOnboardingStore } from '../store/onboarding'
import * as authApi from '../api/auth'
import { submitOnboarding } from '../api/profile'
import { calculateFootprint } from '../api/footprint'

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: ({ email, password }) => authApi.login(email, password),
    onSuccess: (res) => {
      const { access_token, user_id, display_name } = res.data
      setAuth(access_token, user_id, display_name)
      navigate('/home')
    },
  })
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth)
  const seedDefaults = useNotificationStore((s) => s.seedDefaults)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: ({ email, password, display_name }) =>
      authApi.register(email, password, display_name),
    onSuccess: async (res) => {
      const { access_token, user_id, display_name } = res.data
      setAuth(access_token, user_id, display_name)
      seedDefaults()

      // If chat onboarding already gathered data, auto-submit and go to dashboard
      const store = useOnboardingStore.getState()
      if (store.hasData()) {
        try {
          const d = store.data
          await submitOnboarding({
            zip_code: d.zip_code,
            address: d.address || null,
            latitude: d.latitude,
            longitude: d.longitude,
            transport_mode: d.transport_mode,
            commute_days_per_week: d.commute_days_per_week ?? 5,
            diet_type: d.diet_type,
            home_type: d.home_type || 'apartment',
            home_size_sqm: d.home_size_sqm,
            has_pets: d.has_pets ?? false,
            pet_type: d.pet_type,
            pet_count: d.pet_count,
          })
          await calculateFootprint()
          useAuthStore.getState().setZip(d.zip_code)
          if (d.address) useAuthStore.getState().setLocation(d.address, d.latitude, d.longitude)
          store.clear()
          navigate('/home')
        } catch {
          // If auto-submit fails, fall back to wizard
          navigate('/onboarding/zip')
        }
        return
      }

      navigate('/onboarding/zip')
    },
  })
}
