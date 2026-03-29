// Configurazione API backend van_management

export const API_BASE_URL = 'http://localhost:8000';

export const API_HEADERS: Record<string, string> = {
  'Content-Type': 'application/json',
};

// Intervallo polling fleet (millisecondi)
export const POLLING_INTERVAL = 5000;

// Fetch wrapper con header ngrok
export async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: API_HEADERS,
  });

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }

  return response.json();
}
