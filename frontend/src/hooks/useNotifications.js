import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { initNotifications, stopNotifications, markSummaryResponded } from '../utils/notifications'

/**
 * Hook that initializes the notification scheduler and handles
 * SW message-based navigation (notification clicks).
 *
 * Also marks the summary as "responded" whenever the user navigates
 * to a logging page after 20:30.
 */
export function useNotifications() {
  const navigate = useNavigate()

  useEffect(() => {
    initNotifications()

    // Listen for navigation messages from the service worker
    function onMessage(event) {
      if (event.data?.type === 'NAVIGATE') {
        // Mark summary as responded if user is clicking through
        const now = new Date()
        if (now.getHours() >= 20) {
          markSummaryResponded()
        }
        navigate(event.data.url)
      }
    }

    navigator.serviceWorker?.addEventListener('message', onMessage)

    return () => {
      stopNotifications()
      navigator.serviceWorker?.removeEventListener('message', onMessage)
    }
  }, [navigate])
}
