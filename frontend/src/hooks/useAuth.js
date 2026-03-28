import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import * as authApi from '../api/auth'

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
  const navigate = useNavigate()

  return useMutation({
    mutationFn: ({ email, password, display_name }) =>
      authApi.register(email, password, display_name),
    onSuccess: (res) => {
      const { access_token, user_id, display_name } = res.data
      setAuth(access_token, user_id, display_name)
      navigate('/onboarding/zip')
    },
  })
}
