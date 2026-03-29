import { Achievement } from '../types';

// Achievement disponibili nel sistema
export const ACHIEVEMENTS: Achievement[] = [
  {
    id: 'first_report',
    label: 'Prima Segnalazione',
    description: 'Invia il tuo primo report',
    icon: 'flag',
    unlockedAt: '2026-03-15T10:00:00Z',
  },
  {
    id: 'eco_warrior',
    label: 'Eco Warrior',
    description: '10 segnalazioni totali',
    icon: 'military-tech',
    unlockedAt: '2026-03-20T14:30:00Z',
  },
  {
    id: 'model_citizen',
    label: 'Cittadino Modello',
    description: '50 segnalazioni totali',
    icon: 'auto-awesome',
  },
  {
    id: 'streak_7',
    label: '7 Day Streak',
    description: '7 giorni consecutivi con almeno 1 segnalazione',
    icon: 'local-fire-department',
    unlockedAt: '2026-03-25T09:00:00Z',
  },
  {
    id: 'community_star',
    label: 'Community Star',
    description: 'Entra nella top 10 della classifica settimanale',
    icon: 'volunteer-activism',
  },
  {
    id: 'plastic_pro',
    label: 'Plastic Pro',
    description: '20 segnalazioni di tipo plastica',
    icon: 'recycling',
  },
];
