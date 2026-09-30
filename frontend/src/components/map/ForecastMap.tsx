import type { ReactNode } from 'react'
import { MapContainer, Pane, TileLayer, ZoomControl } from 'react-leaflet'

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

export function ForecastMap({ children }: { children: ReactNode }) {
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
      className="absolute inset-0 z-0"
    >
      <TileLayer url={BASE_URL} attribution={ATTRIBUTION} maxNativeZoom={16} />
      {children}
      {/* Labels above the heatmap so place names stay readable */}
      <Pane name="labels" style={{ zIndex: 450, pointerEvents: 'none' }}>
        <TileLayer url={LABELS_URL} maxNativeZoom={16} />
      </Pane>
      <ZoomControl position="bottomright" />
    </MapContainer>
  )
}
