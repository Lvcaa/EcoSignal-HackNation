import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user_id: null,
      display_name: null,
      zip_code: null,
      address: null,
      latitude: null,
      longitude: null,
      original_auth: null, // saved when impersonating
      setAuth: (token, user_id, display_name) =>
        set({ token, user_id, display_name }),
      setZip: (zip_code) => set({ zip_code }),
      setLocation: (address, latitude, longitude) =>
        set({ address, latitude, longitude }),
      startImpersonation: (newToken, newUserId, newName) =>
        set((state) => ({
          original_auth: state.original_auth || {
            token: state.token,
            user_id: state.user_id,
            display_name: state.display_name,
            zip_code: state.zip_code,
            address: state.address,
            latitude: state.latitude,
            longitude: state.longitude,
          },
          token: newToken,
          user_id: newUserId,
          display_name: newName,
        })),
      stopImpersonation: () =>
        set((state) => {
          if (!state.original_auth) return {}
          return { ...state.original_auth, original_auth: null }
        }),
      logout: () =>
        set({ token: null, user_id: null, display_name: null, zip_code: null, address: null, latitude: null, longitude: null, original_auth: null }),
    }),
    { name: 'ecosignal-auth' }
  )
)
