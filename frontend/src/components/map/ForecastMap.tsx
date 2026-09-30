import type { ReactNode } from 'react'
import type { GeoJsonObject } from 'geojson'
import { GeoJSON, MapContainer, Pane, TileLayer, ZoomControl, useMapEvents } from 'react-leaflet'
import indiaBoundaryData from '../../data/india-boundary.json'
import indiaMaskData from '../../data/india-mask.json'

const INDIA_GEOJSON = indiaBoundaryData as unknown as GeoJsonObject
const INDIA_MASK_GEOJSON = indiaMaskData as unknown as GeoJsonObject

// Esri Canvas Dark Gray: keyless (CARTO basemaps now watermark tiles with "API KEY REQUIRED")
const ESRI_CANVAS = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas'
const BASE_URL = `${ESRI_CANVAS}/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`
const LABELS_URL = `${ESRI_CANVAS}/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`
const ATTRIBUTION = 'Tiles &copy; <a href="https://www.esri.com">Esri</a> &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors'

const INDIA_CENTER: [number, number] = [23, 82]
const MAX_BOUNDS: [[number, number], [number, number]] = [
  [0, 55],
  [45, 110],
]

function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

export function ForecastMap({
  children,
  onMapClick,
}: {
  children: ReactNode
  onMapClick?: (lat: number, lon: number) => void
}) {
  return (
    <MapContainer
      center={INDIA_CENTER}
      zoom={5}
      minZoom={4}
      maxZoom={10}
      maxBounds={MAX_BOUNDS}
      maxBoundsViscosity={0.8}
      zoomControl={false}
      preferCanvas
      className="absolute inset-0 z-0 print:hidden"
    >
      <TileLayer url={BASE_URL} attribution={ATTRIBUTION} maxNativeZoom={16} />
      {onMapClick && <MapClickHandler onMapClick={onMapClick} />}
      {children}
      {/* Dim outer surroundings outside India to elevate the subcontinent */}
      <Pane name="india-focus-mask" style={{ zIndex: 440, pointerEvents: 'none' }}>
        <GeoJSON
          data={INDIA_MASK_GEOJSON}
          style={{
            fillColor: '#020617',
            fillOpacity: 0.38,
            stroke: false,
          }}
        />
      </Pane>
      {/* Labels above the heatmap and mask so place names stay readable */}
      <Pane name="labels" style={{ zIndex: 450, pointerEvents: 'none' }}>
        <TileLayer url={LABELS_URL} maxNativeZoom={16} />
      </Pane>
      {/* Official Survey of India national boundary (visible through and on top of forecast overlays) */}
      <Pane
        name="india-border"
        style={{
          zIndex: 460,
          pointerEvents: 'none',
          filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.95)) drop-shadow(0 6px 14px rgba(0, 0, 0, 0.85))',
        }}
      >
        {/* Deep dark halo backing for contrast over bright weather cells */}
        <GeoJSON
          data={INDIA_GEOJSON}
          style={{
            color: '#000000',
            weight: 4.5,
            opacity: 0.85,
            fillColor: 'transparent',
            fillOpacity: 0,
          }}
        />
        {/* Crisp platinum national border matching the dark cartographic basemap */}
        <GeoJSON
          data={INDIA_GEOJSON}
          style={{
            color: '#f8fafc',
            weight: 1.8,
            opacity: 0.95,
            fillColor: 'transparent',
            fillOpacity: 0,
          }}
        />
      </Pane>
      <ZoomControl position="bottomright" />
    </MapContainer>
  )
}
