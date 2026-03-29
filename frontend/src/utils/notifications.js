/**
 * EcoSignal Notification Scheduler
 *
 * Schedules local web notifications at specific times:
 *  - 08:00  → Log breakfast
 *  - 12:30  → Log lunch
 *  - 19:30  → Log dinner
 *  - 20:30  → Daily summary request
 *  - 21:00  → If no action logged since 20:30, show CO2 tip instead
 */

const STORAGE_KEY = 'eco_notifications_sent'
const SUMMARY_RESPONDED_KEY = 'eco_summary_responded'

const CO2_TIPS = [
  'Spegni le luci quando esci da una stanza: risparmi fino a 40 kg di CO₂ all\'anno.',
  'Usa la bicicletta per tragitti sotto i 5 km: zero emissioni e più salute!',
  'Riduci il consumo di carne rossa: un pasto vegetariano risparmia circa 2,5 kg di CO₂.',
  'Abbassa il termostato di 1°C: risparmi fino al 7% di energia per il riscaldamento.',
  'Usa borse riutilizzabili: ogni borsa di plastica evitata risparmia 33 g di CO₂.',
  'Fai docce più brevi (5 min): risparmi circa 350 kg di CO₂ all\'anno.',
  'Stendi il bucato all\'aria invece di usare l\'asciugatrice: risparmi 2,4 kg di CO₂ per ciclo.',
  'Compra prodotti locali e di stagione: meno trasporto = meno emissioni.',
  'Spegni gli elettrodomestici in standby: risparmi fino a 100 kg di CO₂ all\'anno.',
  'Porta il pranzo da casa in un contenitore riutilizzabile invece di comprare cibo confezionato.',
  'Usa l\'acqua fredda per lavare i vestiti: il 90% dell\'energia della lavatrice va nel riscaldamento.',
  'Pianta un albero: assorbe circa 22 kg di CO₂ all\'anno.',
  'Condividi i viaggi in auto con colleghi: dimezzi le emissioni per persona.',
  'Ripara invece di sostituire: allungare la vita di un oggetto riduce le emissioni di produzione.',
  'Scegli energia rinnovabile: il passaggio al verde può azzerare le emissioni domestiche.',
]

/** Returns today as YYYY-MM-DD */
function todayKey() {
  return new Date().toISOString().slice(0, 10)
}

/** Get the set of notification IDs already sent today */
function getSentToday() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    if (parsed._date !== todayKey()) return {}
    return parsed
  } catch {
    return {}
  }
}

/** Mark a notification ID as sent today */
function markSent(id) {
  const sent = getSentToday()
  sent._date = todayKey()
  sent[id] = true
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sent))
}

/** Check if the user responded to the 20:30 summary notification */
export function markSummaryResponded() {
  localStorage.setItem(SUMMARY_RESPONDED_KEY, todayKey())
}

function hasSummaryResponse() {
  return localStorage.getItem(SUMMARY_RESPONDED_KEY) === todayKey()
}

function getRandomTip() {
  return CO2_TIPS[Math.floor(Math.random() * CO2_TIPS.length)]
}

/** Show a web notification */
async function showNotification(title, body, url) {
  if (Notification.permission !== 'granted') return

  const reg = await navigator.serviceWorker?.ready
  if (reg) {
    reg.showNotification(title, {
      body,
      icon: '/green-buddy-logo.png',
      badge: '/green-buddy-logo.png',
      tag: 'ecosignal-' + Date.now(),
      data: { url },
      requireInteraction: true,
    })
  } else {
    // Fallback: direct Notification API (no click-to-navigate)
    new Notification(title, {
      body,
      icon: '/green-buddy-logo.png',
    })
  }
}

/** Core schedule definitions */
const MEAL_NOTIFICATIONS = [
  { id: 'breakfast', hour: 8, minute: 0, title: 'Buongiorno!', body: 'Registra la tua colazione per tracciare l\'impatto ambientale.', url: '/actions/meal' },
  { id: 'lunch', hour: 12, minute: 30, title: 'Buon appetito!', body: 'È ora di pranzo! Registra il tuo pasto.', url: '/actions/meal' },
  { id: 'dinner', hour: 19, minute: 30, title: 'Buonasera!', body: 'Registra la tua cena per completare la giornata.', url: '/actions/meal' },
]

const SUMMARY_NOTIFICATION = {
  id: 'summary', hour: 20, minute: 30,
  title: 'Com\'è andata la giornata?',
  body: 'Registra un riepilogo delle attività di oggi e scopri il tuo impatto.',
  url: '/home',
}

const TIP_NOTIFICATION = {
  id: 'tip', hour: 21, minute: 0,
}

/** Check current time and fire any due notifications */
function checkSchedule() {
  const now = new Date()
  const h = now.getHours()
  const m = now.getMinutes()
  const sent = getSentToday()

  // Meal notifications — fire if within 5-minute window
  for (const notif of MEAL_NOTIFICATIONS) {
    if (sent[notif.id]) continue
    if (h === notif.hour && m >= notif.minute && m < notif.minute + 5) {
      markSent(notif.id)
      showNotification(notif.title, notif.body, notif.url)
    }
  }

  // Summary notification at 20:30
  if (!sent[SUMMARY_NOTIFICATION.id]) {
    if (h === SUMMARY_NOTIFICATION.hour && m >= SUMMARY_NOTIFICATION.minute && m < SUMMARY_NOTIFICATION.minute + 5) {
      markSent(SUMMARY_NOTIFICATION.id)
      showNotification(SUMMARY_NOTIFICATION.title, SUMMARY_NOTIFICATION.body, SUMMARY_NOTIFICATION.url)
    }
  }

  // CO2 tip at 21:00 — only if summary was sent but user didn't respond
  if (!sent[TIP_NOTIFICATION.id] && sent[SUMMARY_NOTIFICATION.id]) {
    if (h === TIP_NOTIFICATION.hour && m >= TIP_NOTIFICATION.minute && m < TIP_NOTIFICATION.minute + 5) {
      if (!hasSummaryResponse()) {
        markSent(TIP_NOTIFICATION.id)
        showNotification(
          'Consiglio verde del giorno',
          getRandomTip(),
          '/home',
        )
      }
    }
  }
}

let intervalId = null

/** Request permission and start the scheduler */
export async function initNotifications() {
  if (!('Notification' in window)) return

  if (Notification.permission === 'default') {
    await Notification.requestPermission()
  }

  if (Notification.permission !== 'granted') return

  // Register service worker
  if ('serviceWorker' in navigator) {
    try {
      await navigator.serviceWorker.register('/sw.js')
    } catch (e) {
      console.warn('SW registration failed:', e)
    }
  }

  // Check immediately, then every 30 seconds
  checkSchedule()
  if (intervalId) clearInterval(intervalId)
  intervalId = setInterval(checkSchedule, 30_000)
}

/** Stop the scheduler */
export function stopNotifications() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}
