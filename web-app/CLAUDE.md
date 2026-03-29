# WasteTrack — Contesto progetto per Claude Code

## Cos'è
App mobile per tracciare i camion della spazzatura in tempo reale su mappa,
con gamification per incentivare i cittadini a segnalare problemi (cestini pieni, ecc.).

Sviluppata da Luis (Head of R&D). **Solo frontend** — il backend lo gestisce un altro team.
Le API (REST + WebSocket) arriveranno in seguito: per ora si usano dati mock che rispettano
già la forma definitiva dei tipi, così il passaggio sarà un rimpiazzo 1:1.

---

## Stack tecnico

| Layer | Tecnologia |
|---|---|
| Framework | Expo SDK 51 + TypeScript |
| Mappa | react-native-maps (Google Maps, stile iOS nativo) |
| Bottom sheet | @gorhom/bottom-sheet |
| Navigazione | react-navigation v6 — bottom tab navigator |
| Auth | Clerk o Supabase Auth (da decidere) |
| UI | Stile iOS nativo puro — nessuna libreria UI esterna |

---

## Struttura cartelle

```
src/
  screens/
    MapScreen.tsx
    ReportsScreen.tsx
    LeaderboardScreen.tsx
    ProfileScreen.tsx
  components/
    TruckMarker.tsx
    TruckBottomSheet.tsx
    FilterPills.tsx
    ReportCard.tsx
    BadgeGrid.tsx
    XPBar.tsx
  hooks/
    useTrucks.ts
    useReports.ts
    useUser.ts
  data/
    trucks.ts        ← mock
    reports.ts       ← mock
    users.ts         ← mock
    achievements.ts  ← lista achievement disponibili
  types/
    index.ts         ← tutte le TypeScript interface
  navigation/
    TabNavigator.tsx
```

---

## Schermate — 4 tab

### 1. Mappa (home)
- Mappa fullscreen con `StyleSheet.absoluteFillObject`
- Marker camion animati in tempo reale (mock → WebSocket)
- Tap su marker → bottom sheet con:
  - Tipo rifiuto (organico / plastica / indifferenziato / misto)
  - Percentuale carico (progress bar)
  - Prossima fermata + ETA
  - Percorso del camion come polyline sulla mappa
- Filtri in alto (pill): Tutti · Organico · Plastica · Misto
- Badge top-right: "X camion attivi"

### 2. Segnalazioni
- Lista report dell'utente con stato (Inviata / In lavorazione / Risolta)
- Ogni card: indirizzo, foto thumbnail, timestamp, XP guadagnati
- FAB bottom-right → flusso nuova segnalazione:
  1. Seleziona cestino su mappa (o usa GPS)
  2. Foto opzionale (camera o galleria)
  3. Conferma → invio → toast "+10 XP"

### 3. Classifica
- Segmented control: Weekly / Monthly / All-time
- Top 3 con podio (avatar, username, punti)
- Lista completa sotto con rank, livello, punti
- Scroll orizzontale achievement badge (lock/unlock)
- Utente corrente sempre evidenziato

### 4. Profilo
- Avatar + nome + livello attuale
- Barra XP con progresso verso livello successivo
- Griglia badge sbloccati
- Lista storico segnalazioni personali

---

## Tipi TypeScript (forma definitiva — usare anche nei mock)

```typescript
type WasteType = 'organic' | 'plastic' | 'mixed' | 'hazardous';

interface Truck {
  id: string;
  lat: number;
  lng: number;
  wasteType: WasteType;
  loadPercent: number;       // 0–100
  nextStop: string;
  eta: string;               // es. "12 min"
  route: { lat: number; lng: number }[];
  status: 'active' | 'full' | 'offline';
}

interface Report {
  id: string;
  userId: string;
  binId: string;
  lat: number;
  lng: number;
  photo?: string;            // URI locale o URL remoto
  status: 'sent' | 'in_progress' | 'resolved';
  xp: number;
  createdAt: string;         // ISO 8601
}

interface User {
  id: string;
  name: string;
  avatar: string;
  xp: number;
  level: number;
  badges: Achievement[];
}

interface Achievement {
  id: string;
  label: string;
  description: string;
  icon: string;
  unlockedAt?: string;       // assente = bloccato
}

interface LeaderboardEntry {
  rank: number;
  user: Pick<User, 'id' | 'name' | 'avatar' | 'level'>;
  points: number;
  pointsToday?: number;
}
```

---

## Gamification

| Azione | XP |
|---|---|
| Prima segnalazione | +20 XP |
| Segnalazione normale | +10 XP |
| Segnalazione risolta | +5 XP bonus |
| 7 giorni consecutivi | +50 XP |

### Achievement disponibili
- **Prima segnalazione** — invia il primo report
- **Eco Warrior** — 10 segnalazioni totali
- **Cittadino modello** — 50 segnalazioni totali
- **7 Day Streak** — 7 giorni consecutivi con almeno 1 segnalazione
- **Community Star** — entra nella top 10 della classifica settimanale
- **Plastic Pro** — 20 segnalazioni di tipo plastica

---

## Stile e design

- **Palette**: bianco `#FFFFFF`, blu azione `#007AFF`, grigio superfici `#F2F2F7`, testo `#000000`
- **Font**: SF Pro (sistema iOS — nativo automatico)
- **Componenti**: iOS nativi — niente librerie UI esterne
- **Border radius**: 12–16pt per card, 20pt per bottom sheet
- **Niente**: neon, dark theme forzato, glassmorphism, gradienti decorativi

---

## Convenzioni codice

- Componenti in **PascalCase**
- Hook con prefisso **use** (es. `useTrucks`)
- Stili con `StyleSheet.create` — niente inline styles
- I mock in `src/data/` rispettano **esattamente** i tipi TypeScript
- Nessuna logica di business nei componenti — va negli hook
- Commenti in italiano

---

## Stato avanzamento

- [ ] Scaffold Expo + TypeScript + navigazione tab
- [ ] Tipi TypeScript + dati mock
- [ ] MapScreen — mappa base + marker mock
- [ ] MapScreen — bottom sheet dettaglio camion
- [ ] MapScreen — polyline percorso + filtri pill
- [ ] ReportsScreen — lista + FAB + flusso nuovo report
- [ ] LeaderboardScreen — classifica + achievement
- [ ] ProfileScreen — XP bar + badge + storico
- [ ] Auth (Google + Apple + Email)
- [ ] Integrazione API reale (rimpiazzo mock)
