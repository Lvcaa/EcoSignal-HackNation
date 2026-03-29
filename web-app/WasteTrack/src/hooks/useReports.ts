import { useState, useCallback } from 'react';
import { Report } from '../types';
import { MOCK_REPORTS } from '../data/reports';

interface UseReportsResult {
  reports: Report[];
  totalPoints: number;
  resolvedCount: number;
  addReport: (report: Omit<Report, 'id' | 'userId' | 'xp' | 'createdAt' | 'status'>) => void;
}

export function useReports(): UseReportsResult {
  const [reports, setReports] = useState<Report[]>(MOCK_REPORTS);

  const totalPoints = reports.reduce((sum, r) => sum + r.xp, 0);
  const resolvedCount = reports.filter((r) => r.status === 'resolved').length;

  const addReport = useCallback(
    (partial: Omit<Report, 'id' | 'userId' | 'xp' | 'createdAt' | 'status'>) => {
      const newReport: Report = {
        ...partial,
        id: `r${Date.now()}`,
        userId: 'u1',
        xp: reports.length === 0 ? 20 : 10, // Prima segnalazione = 20 XP
        createdAt: new Date().toISOString(),
        status: 'sent',
      };
      setReports((prev) => [newReport, ...prev]);
    },
    [reports.length]
  );

  return { reports, totalPoints, resolvedCount, addReport };
}
