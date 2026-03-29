import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useOnboardingStore = create(
  persist(
    (set, get) => ({
      // Profile data gathered during onboarding (chat or wizard)
      data: {
        zip_code: '',
        address: '',
        latitude: null,
        longitude: null,
        transport_mode: 'transit',
        commute_days_per_week: undefined,
        diet_type: 'meat_weekly',
        home_type: '',
        home_size_sqm: 70,
        has_pets: undefined,
        pet_type: null,
        pet_count: 0,
      },

      // Chat conversation history (for Parliamo mode)
      chatMessages: [],

      // Which mode was chosen
      mode: null, // 'chat' | 'quick'

      updateData: (partial) =>
        set((s) => ({ data: { ...s.data, ...partial } })),

      setChatMessages: (messages) => set({ chatMessages: messages }),

      addChatMessage: (msg) =>
        set((s) => ({ chatMessages: [...s.chatMessages, msg] })),

      setMode: (mode) => set({ mode }),

      hasData: () => {
        const d = get().data
        return !!(d.zip_code && d.transport_mode && d.diet_type && d.home_type && d.has_pets !== undefined)
      },

      clear: () =>
        set({
          data: {
            zip_code: '',
            address: '',
            latitude: null,
            longitude: null,
            transport_mode: 'transit',
            commute_days_per_week: undefined,
            diet_type: 'meat_weekly',
            home_type: '',
            home_size_sqm: 70,
            has_pets: undefined,
            pet_type: null,
            pet_count: 0,
          },
          chatMessages: [],
          mode: null,
        }),
    }),
    { name: 'ecosignal-onboarding' }
  )
)
