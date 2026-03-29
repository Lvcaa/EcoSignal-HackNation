import { useState, useEffect } from 'react';
import type { Report } from '../types';

const API_ACTIVE = '/api/v1/reports/active';
const API_RANDOM = '/api/v1/reports/random';

function nextDelay() {
  return 10_000 + Math.random() * 5_000;
}

export function useReports() {
  const [activeReports, setActiveReports] = useState<Report[]>([]);

  useEffect(() => {
    // Prova prima /active; se non disponibile, carica 4 report random in parallelo
    fetch(API_ACTIVE)
      .then((res) => { if (!res.ok) throw new Error(); return res.json(); })
      .then((json) => { if (json.data?.length) setActiveReports(json.data); else throw new Error(); })
      .catch(() => {
        fetch(API_RANDOM)
          .then((r) => r.json())
          .then((j) => { if (j.data) setActiveReports([j.data]); })
          .catch(() => {});
      });
  }, []);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;

    async function fetchAndAdd() {
      try {
        const res = await fetch(API_RANDOM);
        if (!res.ok) throw new Error();
        const json = await res.json();
        const report: Report = json.data;

        setActiveReports((prev) => {
          if (prev.some((r) => r.id === report.id)) return prev;
          return [report, ...prev].slice(0, 20);
        });
      } catch {
        // Silenzioso — riprova al prossimo ciclo
      }

      timeoutId = setTimeout(fetchAndAdd, nextDelay());
    }

    timeoutId = setTimeout(fetchAndAdd, nextDelay());
    return () => clearTimeout(timeoutId);
  }, []);

  return { activeReports };
}
