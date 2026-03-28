import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user_id: null,
      display_name: null,
      zip_code: null,
      setAuth: (token, user_id, display_name) =>
        set({ token, user_id, display_name }),
      setZip: (zip_code) => set({ zip_code }),
      logout: () =>
        set({ token: null, user_id: null, display_name: null, zip_code: null }),
    }),
    { name: 'ecosignal-auth' }
  )
)
