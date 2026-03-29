import { User, LeaderboardEntry } from '../types';
import { ACHIEVEMENTS } from './achievements';

// Utente corrente
export const CURRENT_USER: User = {
  id: 'u1',
  name: 'Alex Rivera',
  avatar: 'https://i.pravatar.cc/150?img=12',
  xp: 1420,
  level: 24,
  title: 'Urban Guardian',
  badges: ACHIEVEMENTS.filter((a) => a.unlockedAt !== undefined),
};

// XP necessari per livello successivo
export const XP_PER_LEVEL = 2000;

// Classifica mock
export const MOCK_LEADERBOARD: LeaderboardEntry[] = [
  {
    rank: 1,
    user: { id: 'u10', name: 'Marcus T.', avatar: 'https://i.pravatar.cc/150?img=3', level: 32 },
    points: 1850,
    trend: 12,
  },
  {
    rank: 2,
    user: { id: 'u11', name: 'Sarah J.', avatar: 'https://i.pravatar.cc/150?img=5', level: 28 },
    points: 1420,
    trend: 8,
  },
  {
    rank: 3,
    user: { id: 'u12', name: 'Alex W.', avatar: 'https://i.pravatar.cc/150?img=8', level: 26 },
    points: 1280,
    trend: -3,
  },
  {
    rank: 4,
    user: { id: 'u13', name: 'Elena M.', avatar: 'https://i.pravatar.cc/150?img=9', level: 25 },
    points: 1150,
    trend: 5,
  },
  {
    rank: 5,
    user: { id: 'u1', name: 'Alex Rivera', avatar: 'https://i.pravatar.cc/150?img=12', level: 24 },
    points: 1080,
    trend: 15,
  },
  {
    rank: 6,
    user: { id: 'u14', name: 'Luca B.', avatar: 'https://i.pravatar.cc/150?img=11', level: 22 },
    points: 980,
    trend: -2,
  },
  {
    rank: 7,
    user: { id: 'u15', name: 'Giulia R.', avatar: 'https://i.pravatar.cc/150?img=20', level: 21 },
    points: 920,
    trend: 7,
  },
  {
    rank: 8,
    user: { id: 'u16', name: 'Marco P.', avatar: 'https://i.pravatar.cc/150?img=15', level: 19 },
    points: 850,
    trend: 1,
  },
  {
    rank: 9,
    user: { id: 'u17', name: 'Chiara L.', avatar: 'https://i.pravatar.cc/150?img=25', level: 18 },
    points: 780,
    trend: -5,
  },
  {
    rank: 10,
    user: { id: 'u18', name: 'Federico S.', avatar: 'https://i.pravatar.cc/150?img=33', level: 16 },
    points: 720,
    trend: 3,
  },
];
