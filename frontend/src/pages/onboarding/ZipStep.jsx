import { useState, useRef, useCallback } from 'react'
import { useNavigate, useOutletContext } from 'react-router-dom'
import { GoogleMap, useJsApiLoader, MarkerF } from '@react-google-maps/api'
import ProgressDots from '../../components/onboarding/ProgressDots'

const LIBRARIES = ['places']
const MAP_CONTAINER = { width: '100%', height: '100%', borderRadius: '1rem' }
const ITALY_CENTER = { lat: 41.9, lng: 12.5 }

export default function ZipStep() {
  const navigate = useNavigate()
  const { data, updateData } = useOutletContext()
  const [address, setAddress] = useState(data.address || '')
  const [zip, setZip] = useState(data.zip_code || '')
  const [position, setPosition] = useState(
    data.latitude ? { lat: data.latitude, lng: data.longitude } : null
  )
  const [city, setCity] = useState('')
  const inputRef = useRef(null)
  const autocompleteRef = useRef(null)

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '',
    libraries: LIBRARIES,
  })

  const onMapLoad = useCallback(() => {}, [])

  const onAutocompleteMount = useCallback((node) => {
    if (!node || autocompleteRef.current) return
    inputRef.current = node

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
      if (postalCode) setZip(postalCode)
      if (cityName) setCity(cityName)
    })

    autocompleteRef.current = ac
  }, [])

  const hasLocation = position && zip

  const handleNext = () => {
    updateData({
      zip_code: zip,
      address,
      latitude: position?.lat || null,
      longitude: position?.lng || null,
    })
    navigate('/onboarding/transport')
  }

  return (
    <div className="flex flex-col h-full">
      <ProgressDots current={0} total={6} />

      {/* Hero card */}
      <div className="relative rounded-3xl overflow-hidden mb-6 h-40">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/90 to-primary-container/90" />
        <div className="relative z-10 p-5 flex flex-col justify-end h-full text-on-primary">
          <p className="text-xs uppercase tracking-widest font-semibold opacity-80">Cominciamo</p>
          <h2 className="text-xl font-bold mt-1">Personalizza la tua esperienza ambientale</h2>
        </div>
      </div>

      <h3 className="text-lg font-black text-on-surface mb-1">Dove vivi?</h3>
      <p className="text-xs text-on-surface/50 mb-4">
        Il tuo indirizzo ci aiuta a mappare la qualit&agrave; dell&apos;aria e le iniziative green nel tuo quartiere.
      </p>

      {/* Address input with autocomplete */}
      <label className="text-[10px] font-bold text-on-surface/50 uppercase tracking-wider mb-1.5">
        Indirizzo
      </label>
      {isLoaded ? (
        <input
          ref={onAutocompleteMount}
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="es. Via Roma 1, Milano"
          className="w-full px-4 py-3.5 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-sm font-medium"
        />
      ) : (
        <div className="w-full px-4 py-3.5 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 text-sm text-on-surface/40">
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
        <div className="mt-4 rounded-2xl overflow-hidden h-44 bg-surface-container-low">
          <GoogleMap
            mapContainerStyle={MAP_CONTAINER}
            center={position || ITALY_CENTER}
            zoom={position ? 16 : 5}
            onLoad={onMapLoad}
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

      <div className="mt-auto pt-6 flex items-center justify-between">
        <button onClick={() => navigate('/welcome')} className="text-on-surface/50 text-sm font-medium">
          Salta
        </button>
        <button
          onClick={handleNext}
          disabled={!zip || zip.length < 5}
          className="bg-primary text-on-primary font-bold px-8 py-3 rounded-2xl active:scale-95 transition-all ease-out-expo disabled:opacity-40 flex items-center gap-2"
        >
          Prossimo <span className="material-symbols-outlined text-lg">arrow_forward</span>
        </button>
      </div>
    </div>
  )
}
