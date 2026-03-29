import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Default notification schedule seeded on registration.
 * These show the user what daily notifications they'll receive.
 */
const DEFAULT_NOTIFICATIONS = [
  {
    id: 'breakfast',
    time: '08:00',
    icon: 'breakfast_dining',
    title: 'Colazione',
    body: 'Registra la tua colazione per tracciare l\'impatto ambientale.',
    url: '/actions/meal',
    type: 'meal',
  },
  {
    id: 'lunch',
    time: '12:30',
    icon: 'lunch_dining',
    title: 'Pranzo',
    body: 'È ora di pranzo! Registra il tuo pasto.',
    url: '/actions/meal',
    type: 'meal',
  },
  {
    id: 'dinner',
    time: '19:30',
    icon: 'dinner_dining',
    title: 'Cena',
    body: 'Registra la tua cena per completare la giornata.',
    url: '/actions/meal',
    type: 'meal',
  },
  {
    id: 'summary',
    time: '20:30',
    icon: 'summarize',
    title: 'Riepilogo giornata',
    body: 'Com\'è andata la giornata? Registra un riepilogo delle attività di oggi.',
    url: '/home',
    type: 'summary',
  },
  {
    id: 'tip',
    time: '21:00',
    icon: 'lightbulb',
    title: 'Consiglio verde',
    body: 'Se non rispondi al riepilogo entro 30 minuti, riceverai un suggerimento per ridurre la tua impronta di CO₂.',
    url: '/home',
    type: 'tip',
  },
]

export const useNotificationStore = create(
  persist(
    (set, get) => ({
      notifications: [],
      unreadCount: 0,
      panelOpen: false,

      /** Seed default notifications (called on registration) */
      seedDefaults: () => {
        set({
          notifications: DEFAULT_NOTIFICATIONS.map((n) => ({
            ...n,
            read: false,
            seededAt: new Date().toISOString(),
          })),
          unreadCount: DEFAULT_NOTIFICATIONS.length,
        })
      },

      togglePanel: () => set((s) => ({ panelOpen: !s.panelOpen })),
      closePanel: () => set({ panelOpen: false }),

      markRead: (id) => {
        const notifs = get().notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n
        )
        set({
          notifications: notifs,
          unreadCount: notifs.filter((n) => !n.read).length,
        })
      },

      markAllRead: () => {
        set((s) => ({
          notifications: s.notifications.map((n) => ({ ...n, read: true })),
          unreadCount: 0,
        }))
      },

      clearAll: () => set({ notifications: [], unreadCount: 0 }),
    }),
    { name: 'ecosignal-notifications' }
  )
)
