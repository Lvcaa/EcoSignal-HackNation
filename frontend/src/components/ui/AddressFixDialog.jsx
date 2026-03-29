import { useState, useRef, useCallback } from 'react'
import { GoogleMap, useJsApiLoader, MarkerF } from '@react-google-maps/api'
import { useAuthStore } from '../../store/auth'
import { updateProfile } from '../../api/profile'

const LIBRARIES = ['places']
const MAP_CONTAINER = { width: '100%', height: '100%', borderRadius: '0.75rem' }
const ITALY_CENTER = { lat: 41.9, lng: 12.5 }

export default function AddressFixDialog({ onClose }) {
  const { setZip, setLocation } = useAuthStore()
  const [address, setAddress] = useState('')
  const [zip, setZipLocal] = useState('')
  const [position, setPosition] = useState(null)
  const [city, setCity] = useState('')
  const [saving, setSaving] = useState(false)
  const autocompleteRef = useRef(null)

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '',
    libraries: LIBRARIES,
  })

  const onAutocompleteMount = useCallback((node) => {
    if (!node || autocompleteRef.current) return

    const ac = new window.google.maps.places.Autocomplete(node, {
      componentRestrictions: { country: 'it' },
      fields: ['address_components', 'formatted_address', 'geometry'],
      types: ['address'],
    })

    ac.addListener('place_changed', () => {
      const place = ac.getPlace()
      if (!place.geometry) return

      const lat = place.geometry.location.lat()
      const lng = place.geometry.location.lng()
      setPosition({ lat, lng })
      setAddress(place.formatted_address || '')

      let postalCode = ''
      let cityName = ''
      for (const comp of place.address_components || []) {
        if (comp.types.includes('postal_code')) postalCode = comp.long_name
        if (comp.types.includes('locality')) cityName = comp.long_name
        if (!cityName && comp.types.includes('administrative_area_level_3')) cityName = comp.long_name
      }
      if (postalCode) setZipLocal(postalCode)
      if (cityName) setCity(cityName)
    })

    autocompleteRef.current = ac
  }, [])

  const hasLocation = position && zip

  const handleSave = async () => {
    if (!hasLocation) return
    setSaving(true)
    try {
      await updateProfile({
        zip_code: zip,
        address,
        latitude: position.lat,
        longitude: position.lng,
      })
      setZip(zip)
      setLocation(address, position.lat, position.lng)
      onClose()
    } catch {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      {/* Dialog */}
      <div className="relative bg-surface-container-lowest rounded-t-3xl sm:rounded-3xl w-full max-w-md max-h-[85vh] overflow-y-auto p-5 pb-8 shadow-xl animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-amber-600 text-2xl">warning</span>
            <h3 className="text-lg font-bold text-on-surface">Imposta il tuo indirizzo</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-surface-container-low">
            <span className="material-symbols-outlined text-on-surface/50">close</span>
          </button>
        </div>

        <p className="text-sm text-on-surface/60 mb-4">
          Il tuo indirizzo non è stato impostato correttamente. Cercalo su Google Maps per avere dati ambientali precisi sul tuo quartiere.
        </p>

        {/* Address input */}
        <label className="text-[10px] font-bold text-on-surface/50 uppercase tracking-wider mb-1.5 block">
          Cerca il tuo indirizzo
        </label>
        {isLoaded ? (
          <input
            ref={onAutocompleteMount}
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="es. Via Roma 1, Milano"
            className="w-full px-4 py-3 rounded-2xl bg-surface-container-low border border-outline-variant/40 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-sm font-medium"
          />
        ) : (
          <div className="w-full px-4 py-3 rounded-2xl bg-surface-container-low border border-outline-variant/40 text-sm text-on-surface/40">
            Caricamento mappa...
          </div>
        )}

        {/* Location confirmation */}
        {hasLocation && (
          <div className="flex items-center gap-3 mt-3 p-3 rounded-2xl bg-surface-container-low">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
              location_on
            </span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-on-surface">{city || 'Posizione trovata'}</p>
              <p className="text-xs text-on-surface/50">CAP {zip}</p>
            </div>
            <span className="material-symbols-outlined text-primary text-lg">check_circle</span>
          </div>
        )}

        {/* Map preview */}
        {isLoaded && (
          <div className="mt-4 rounded-xl overflow-hidden h-36 bg-surface-container-low">
            <GoogleMap
              mapContainerStyle={MAP_CONTAINER}
              center={position || ITALY_CENTER}
              zoom={position ? 16 : 5}
              options={{
                disableDefaultUI: true,
                zoomControl: true,
                mapTypeControl: false,
                streetViewControl: false,
                styles: [
                  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
                  { featureType: 'transit', stylers: [{ visibility: 'off' }] },
                ],
              }}
            >
              {position && <MarkerF position={position} />}
            </GoogleMap>
          </div>
        )}

        {/* Actions */}
        <div className="mt-5 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 rounded-2xl text-sm font-bold text-on-surface/60 bg-surface-container-low active:scale-95 transition-transform"
          >
            Dopo
          </button>
          <button
            onClick={handleSave}
            disabled={!hasLocation || saving}
            className="flex-1 py-3 rounded-2xl text-sm font-bold text-on-primary bg-primary active:scale-95 transition-all disabled:opacity-40 flex items-center justify-center gap-2"
          >
            {saving ? (
              <span className="material-symbols-outlined animate-spin text-lg">progress_activity</span>
            ) : (
              <>
                Conferma
                <span className="material-symbols-outlined text-lg">check</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
