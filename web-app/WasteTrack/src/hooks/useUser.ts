import { useState } from 'react';
import { User } from '../types';
import { CURRENT_USER, XP_PER_LEVEL } from '../data/users';

interface UseUserResult {
  user: User;
  xpProgress: number; // 0-1, progresso verso livello successivo
  xpToNextLevel: number;
}

export function useUser(): UseUserResult {
  const [user] = useState<User>(CURRENT_USER);

  const xpInCurrentLevel = user.xp % XP_PER_LEVEL;
  const xpProgress = xpInCurrentLevel / XP_PER_LEVEL;
  const xpToNextLevel = XP_PER_LEVEL - xpInCurrentLevel;

  return { user, xpProgress, xpToNextLevel };
}
